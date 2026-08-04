"""敏感字段脱敏 — 核心引擎

参考 Archery (sql/utils/data_masking.py) 的 simple_column_mask 实现：
- 按列名（不区分大小写）匹配脱敏规则
- 用正则分组替换命中列的值
- 通用三段式规则(rule_type=100)按长度自动三等分
"""

import math
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger

from .model import DataMaskingColumnModel, DataMaskingRuleModel


async def apply_masking(
    config_id: int,
    columns: list[str],
    rows: list[list],
    db: AsyncSession,
    sql: str = "",
) -> tuple[list[list], list[dict]]:
    """对查询结果应用脱敏。

    Args:
        config_id: 数据源配置 ID
        columns: 列名列表
        rows: 数据行列表
        db: 数据库会话
        sql: 原始 SQL 语句，用于解析表名进行精确匹配

    Returns:
        (脱敏后的 rows, 命中的脱敏列信息列表)
        masked_info 为空列表时表示无需脱敏。
    """
    # 0. 从 SQL 解析 (schema, table) 对（用于按表过滤脱敏配置）
    parsed_tables = _parse_table_names(sql)
    parsed_tables_lower = {(s.lower() if s else None, t.lower()) for s, t in parsed_tables}
    parsed_table_names_lower = {t for _, t in parsed_tables_lower}

    # 1. 查询该数据源下激活的脱敏字段配置
    col_result = await db.execute(
        select(DataMaskingColumnModel).where(
            DataMaskingColumnModel.config_id == config_id,
            DataMaskingColumnModel.active == True,  # noqa: E712
        )
    )
    masking_columns = col_result.scalars().all()
    if not masking_columns:
        return rows, []

    # 2. 按表名+schema 过滤脱敏配置（* 通配）
    # 同一列只保留最精确的配置（schema+table > table-only > wildcard）
    if parsed_tables_lower:
        sql_has_schema = any(s is not None for s, _ in parsed_tables_lower)
        filtered = []
        for mc in masking_columns:
            cfg_table = mc.table_name.lower()
            cfg_schema = mc.table_schema.lower()

            # 表名匹配：* 通配所有表，否则精确匹配
            table_match = cfg_table == "*" or cfg_table in parsed_table_names_lower
            if not table_match:
                continue

            # schema 匹配
            if cfg_schema == "*":
                filtered.append(mc)
            elif sql_has_schema:
                # SQL 有 schema 前缀时，精确匹配
                for sql_schema, sql_table in parsed_tables_lower:
                    if sql_table == cfg_table and sql_schema == cfg_schema:
                        filtered.append(mc)
                        break
            else:
                # SQL 无 schema 前缀时，按表名匹配（兼容不写 schema 的查询习惯）
                filtered.append(mc)

        # 去重：同一列只保留最精确的配置（table_name 非 * 优先）
        column_best: dict[str, Any] = {}
        for mc in filtered:
            key = mc.column_name.lower()
            existing = column_best.get(key)
            if existing is None:
                column_best[key] = mc
            else:
                # 优先保留 table_name 更精确的配置（非 * 优先于 *）
                if existing.table_name == "*" and mc.table_name != "*":
                    column_best[key] = mc

        masking_columns = list(column_best.values())
        if not masking_columns:
            return rows, []

    # 2. 加载所有关联的脱敏规则
    rule_types = {mc.rule_type for mc in masking_columns}
    rule_result = await db.execute(
        select(DataMaskingRuleModel).where(
            DataMaskingRuleModel.rule_type.in_(rule_types)
        )
    )
    rules_map = {r.rule_type: r for r in rule_result.scalars().all()}

    # 3. 按列名匹配（不区分大小写）
    columns_lower = [c.lower() for c in columns]
    masked_rows = [list(row) for row in rows]  # 深拷贝
    masked_info: list[dict] = []

    for mc in masking_columns:
        col_name_lower = mc.column_name.lower()
        rule = rules_map.get(mc.rule_type)
        if not rule:
            continue

        # 查找匹配的列索引
        matching_indices: list[int] = []
        for idx, col_lower in enumerate(columns_lower):
            if col_lower == col_name_lower:
                matching_indices.append(idx)

        if not matching_indices:
            continue

        # 记录命中信息
        masked_info.append({
            "column_name": mc.column_name,
            "rule_type": mc.rule_type,
            "rule_desc": rule.rule_desc,
            "indices": matching_indices,
        })

        # 4. 对命中的列应用脱敏
        if rule.rule_type == 100:
            # 通用三段式：每个值按长度动态构建精确量词正则
            for col_idx in matching_indices:
                for row_idx in range(len(masked_rows)):
                    val = masked_rows[row_idx][col_idx]
                    if val is None or (isinstance(val, str) and not val.strip()):
                        continue
                    compiled = _build_three_part_regex(len(str(val)))
                    if compiled:
                        masked_rows[row_idx][col_idx] = _apply_compiled_mask(
                            compiled, rule.hide_group, val,
                        )
        else:
            # 普通规则：预编译一次，所有行复用
            compiled = _compile_regex(rule.rule_regex)
            if compiled is None:
                continue
            for col_idx in matching_indices:
                for row_idx in range(len(masked_rows)):
                    masked_rows[row_idx][col_idx] = _apply_compiled_mask(
                        compiled, rule.hide_group, masked_rows[row_idx][col_idx],
                    )

    return masked_rows, masked_info


def regex_mask(
    rule_regex: str,
    hide_group: int,
    value: Any,
    rule_type: int = 0,
) -> Any:
    """正则分组脱敏（便捷入口，内部调用 _compile_regex + _apply_compiled_mask）"""
    if rule_type == 100 and value is not None:
        compiled = _build_three_part_regex(len(str(value)))
    else:
        compiled = _compile_regex(rule_regex)
    if compiled is None:
        return value
    return _apply_compiled_mask(compiled, hide_group, value)


def _compile_regex(rule_regex: str) -> re.Pattern | None:
    """预编译正则。返回 None 表示正则无效。"""
    try:
        return re.compile(rule_regex, re.I)
    except re.error:
        return None


def _build_three_part_regex(value_len: int) -> re.Pattern | None:
    """为通用三段式规则(rule_type=100)构建精确量词正则。"""
    if value_len < 3:
        return None
    avg = math.floor(value_len / 3)
    remainder = value_len % 3
    a1 = str(avg)
    a2 = str(avg + (1 if remainder > 0 else 0))
    a3 = str(avg + (1 if remainder > 1 else 0))
    # 精确量词 {n}，无回溯风险
    pattern = r"^([\s\S]{" + a1 + r"})([\s\S]{" + a2 + r"})([\s\S]{" + a3 + r"})$"
    try:
        return re.compile(pattern)
    except re.error:
        return None


def _apply_compiled_mask(
    compiled: re.Pattern,
    hide_group: int,
    value: Any,
) -> Any:
    """用已编译正则对值进行脱敏。

    修复:
    - #2: 捕获 TypeError/IndexError（交替组未参与时 group() 返回 None）
    - #6: hide_group 超出分组数时返回原值并记录警告
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return value

    try:
        m = compiled.search(str(value))
        if m is None or m.lastindex is None:
            return value

        if hide_group > m.lastindex:
            logger.warning(
                "hide_group={} 超出正则分组数={}，跳过脱敏",
                hide_group, m.lastindex,
            )
            return value

        masking_str = ""
        for i in range(m.lastindex):
            group_val = m.group(i + 1)
            if group_val is None:
                # 交替组未参与匹配，视为空字符串
                group_val = ""
            if i == hide_group - 1:
                masking_str += "*" * len(group_val)
            else:
                masking_str += group_val
        return masking_str
    except (AttributeError, re.error, TypeError, IndexError):
        return value


def _parse_table_names(sql: str) -> set[tuple[str | None, str]]:
    """从 SQL 中解析 (schema, table) 对。

    支持:
    - FROM table_name           → (None, 'table_name')
    - FROM schema.table_name    → ('schema', 'table_name')
    - JOIN schema.table_name    → ('schema', 'table_name')

    返回 (schema, table) 元组集合，schema 为 None 表示未指定。
    """
    if not sql:
        return set()

    tables: set[tuple[str | None, str]] = set()
    pattern = re.compile(
        r'(?:FROM|JOIN)\s+'
        r'(?:"?([\w$#]+)"?\."?([\w$#]+)"?'   # schema.table (Oracle supports $ and #)
        r'|"?([\w$#]+)"?)',                    # table only
        re.IGNORECASE,
    )
    for match in pattern.finditer(sql):
        schema = match.group(1)
        table = match.group(2) or match.group(3)
        if table and table.upper() not in ('DUAL', 'SELECT', 'WHERE', 'SET', 'INTO'):
            tables.add((schema, table))

    return tables
