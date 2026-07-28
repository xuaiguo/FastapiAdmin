"""Oracle 表空间查询 CRUD"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import OracleTablespaceOutSchema

# 允许排序的列白名单（防止 SQL 注入）
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset({
    "tablespace_type", "tablespace_name", "autoext",
    "max_mb", "os_file_mb", "used_mb", "pct_used",
})

# 基础 CTE 查询（固定部分，查询 Oracle 系统视图）
_BASE_SQL = """
WITH base AS (
  SELECT 'USER' AS tablespace_type,
         a.tablespace_name,
         a.autoext,
         a.bytes_alloc - NVL(b.bytes_free, 0) AS used_mb,
         a.maxbytes AS max_mb,
         a.bytes_alloc AS os_file_mb
  FROM (
    SELECT f.tablespace_name,
           f.autoextensible AS autoext,
           TRUNC(SUM(f.bytes) / POWER(2, 20)) AS bytes_alloc,
           TRUNC(SUM(DECODE(f.autoextensible, 'YES', f.maxbytes, 'NO', f.bytes)) / POWER(2, 20)) AS maxbytes
    FROM dba_data_files f
    GROUP BY f.tablespace_name, f.autoextensible
  ) a
  LEFT JOIN (
    SELECT f.tablespace_name,
           TRUNC(SUM(f.bytes) / POWER(2, 20)) AS bytes_free
    FROM dba_free_space f
    GROUP BY f.tablespace_name
  ) b ON a.tablespace_name = b.tablespace_name

  UNION ALL

  SELECT 'TEMP' AS tablespace_type,
         h.tablespace_name,
         f.autoextensible AS autoext,
         TRUNC(SUM(NVL(p.bytes_used, 0)) / POWER(2, 20)) AS used_mb,
         TRUNC(SUM(DECODE(f.autoextensible, 'YES', f.maxbytes, 'NO', f.bytes)) / POWER(2, 20)) AS max_mb,
         TRUNC(SUM(f.bytes) / POWER(2, 20)) AS os_file_mb
  FROM v$temp_space_header h
  LEFT JOIN v$temp_extent_pool p
    ON p.file_id = h.file_id AND p.tablespace_name = h.tablespace_name
  JOIN dba_temp_files f
    ON f.file_id = h.file_id AND f.tablespace_name = h.tablespace_name
  GROUP BY h.tablespace_name, f.autoextensible
)
"""

_WRAPPER_SQL = """
SELECT tablespace_type, tablespace_name, autoext,
       max_mb, os_file_mb, used_mb,
       ROUND(100 * used_mb / NULLIF(max_mb, 0)) AS pct_used
FROM base
"""


class OracleTablespaceCRUD:
    """Oracle 表空间查询数据层（只读）"""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("tablespace_type"):
                conditions.append("tablespace_type = :ts_type")
                params["ts_type"] = search["tablespace_type"]

            if search.get("tablespace_name"):
                # 转义 LIKE 通配符，防止用户输入 % 或 _ 导致意外匹配
                safe_name = search["tablespace_name"].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                conditions.append("tablespace_name LIKE :ts_name ESCAPE '\\'")
                params["ts_name"] = f"%{safe_name}%"

            pct_min = search.get("pct_used_min")
            pct_max = search.get("pct_used_max")
            if pct_min is not None and pct_max is not None:
                conditions.append("pct_used BETWEEN :pct_min AND :pct_max")
                params["pct_min"] = pct_min
                params["pct_max"] = pct_max
            elif pct_min is not None:
                conditions.append("pct_used >= :pct_min")
                params["pct_min"] = pct_min
            elif pct_max is not None:
                conditions.append("pct_used <= :pct_max")
                params["pct_max"] = pct_max

            used_min = search.get("used_mb_min")
            used_max = search.get("used_mb_max")
            if used_min is not None and used_max is not None:
                conditions.append("used_mb BETWEEN :used_min AND :used_max")
                params["used_min"] = used_min
                params["used_max"] = used_max
            elif used_min is not None:
                conditions.append("used_mb >= :used_min")
                params["used_min"] = used_min
            elif used_max is not None:
                conditions.append("used_mb <= :used_max")
                params["used_max"] = used_max

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    @staticmethod
    def _build_order_clause(order_by: str | None, order_dir: str | None) -> str:
        """根据排序字段和方向构建 ORDER BY 子句，仅允许白名单列"""
        if order_by and order_by in _ALLOWED_ORDER_COLUMNS:
            direction = "ASC" if order_dir and order_dir.lower() == "asc" else "DESC"
            return f"ORDER BY {order_by} {direction} NULLS LAST"
        # 默认排序：使用率降序
        return "ORDER BY pct_used DESC NULLS LAST"

    async def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询表空间信息"""
        where_clause, params = self._build_where_and_params(search)
        subquery = f"SELECT * FROM ({_WRAPPER_SQL}) {where_clause}"
        order_clause = self._build_order_clause(order_by, order_dir)

        # COUNT 查询
        count_sql = text(f"{_BASE_SQL} SELECT COUNT(*) FROM ({subquery})")
        count_result = await self.db.execute(count_sql, params)
        total = count_result.scalar() or 0

        # DATA 查询（带分页和动态排序）
        data_sql = text(
            f"{_BASE_SQL} {subquery} {order_clause} "
            f"OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        )
        data_params = {**params, "offset": offset, "limit": limit}
        data_result = await self.db.execute(data_sql, data_params)
        rows = data_result.fetchall()

        return {
            "page_no": (offset // limit) + 1 if limit else 1,
            "page_size": limit,
            "total": total,
            "items": [
                OracleTablespaceOutSchema(
                    tablespace_type=r[0],
                    tablespace_name=r[1],
                    autoext=r[2],
                    max_mb=float(r[3] or 0),
                    os_file_mb=float(r[4] or 0),
                    used_mb=float(r[5] or 0),
                    pct_used=float(r[6] or 0),
                )
                for r in rows
            ],
            "has_next": offset + limit < total,
        }
