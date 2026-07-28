"""OB Oracle SQL 查询执行器

独立的 SQL 执行工具函数，不修改 core/ob_oracle/ 基础设施。
使用 ob_oracle_manager 获取引擎，通过 engine.connect() 执行 SQL。
"""

import asyncio
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from app.core.logger import logger
from app.core.ob_oracle.database import ob_oracle_manager

# 禁止执行的 SQL 关键字（仅允许 SELECT）
_FORBIDDEN_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
    "MERGE", "GRANT", "REVOKE", "LOCK", "COMMIT", "ROLLBACK", "SAVEPOINT",
    "EXECUTE", "CALL", "BEGIN", "DECLARE",
})


def _check_sql_safety(sql: str) -> None:
    """检查 SQL 安全性，仅允许 SELECT 语句"""
    cleaned = sql.strip().upper()
    if not cleaned.startswith("SELECT") and not cleaned.startswith("WITH"):
        raise ValueError("仅允许执行 SELECT 或 WITH 查询语句")

    if ";" in cleaned:
        parts = [p.strip() for p in cleaned.split(";") if p.strip()]
        if len(parts) > 1:
            raise ValueError("不允许执行多条 SQL 语句")


def _serialize_value(v: Any) -> Any:
    """将 Oracle 返回的特殊类型序列化为可 JSON 化的值"""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, timedelta):
        total = int(v.total_seconds())
        h, m, s = total // 3600, (total % 3600) // 60, total % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    if isinstance(v, bytes):
        return v.hex()
    return str(v)


async def execute_query(config_id: int, sql: str, max_rows: int = 1000) -> dict:
    """执行 SQL 查询并返回结果（15秒超时）"""
    _check_sql_safety(sql)

    engine = await ob_oracle_manager.get_engine(config_id)

    def _execute():
        start = time.time()
        with engine.connect() as conn:
            # 尝试设置 cx_Oracle 连接超时（某些连接可能不支持）
            try:
                if hasattr(conn.connection, 'call_timeout'):
                    conn.connection.call_timeout = 15000
            except Exception:
                # 如果设置失败，继续执行，依赖 asyncio 超时保护
                pass

            result = conn.execute(text(sql))
            columns = list(result.keys())
            raw_rows = result.fetchmany(max_rows + 1)
            elapsed_ms = round((time.time() - start) * 1000, 2)

            truncated = len(raw_rows) > max_rows
            data_rows = raw_rows[:max_rows] if truncated else raw_rows
            rows = [[_serialize_value(v) for v in row] for row in data_rows]

            return {
                "columns": [str(c) for c in columns],
                "rows": rows,
                "total": len(rows),
                "truncated": truncated,
                "elapsed_ms": elapsed_ms,
            }

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_execute),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        logger.warning("SQL 查询超时（15秒）: {}", sql[:100])
        raise ValueError("查询超时（超过15秒），请优化 SQL 语句或添加更严格的过滤条件")
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        # 捕获 cx_Oracle 的超时异常（ORA-01013）
        if "timeout" in error_msg.lower() or "ora-01013" in error_msg.lower():
            logger.warning("SQL 查询超时（15秒）: {}", sql[:100])
            raise ValueError("查询超时（超过15秒），请优化 SQL 语句或添加更严格的过滤条件")
        logger.error("SQL 执行失败: {}", e, exc_info=True)
        raise ValueError(f"SQL 执行失败: {e}")
