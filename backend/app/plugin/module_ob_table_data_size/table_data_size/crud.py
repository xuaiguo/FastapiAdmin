"""OB 租户表大小统计 CRUD — 查询 DBA_OB_TABLE_LOCATIONS / DBA_OB_TABLET_REPLICAS / DBA_OBJECTS 视图"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schema import ObTableDataSizeOutSchema

# 允许排序的列白名单（防 SQL 注入）
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset({
    "SVR_IP", "DATABASE_NAME", "OBJECT_TYPE", "OBJECT_NAME",
    "DATA_SIZE_MB", "REQUIRED_SIZE_MB",
})

# 固定基础 SQL（3 表 JOIN + 固定过滤条件），动态 WHERE 条件需插在 GROUP BY 之前
_BASE_SQL = """
SELECT
    /*+ READ_CONSISTENCY(WEAK) QUERY_TIMEOUT(50000000) */
    a.SVR_IP,
    a.SVR_PORT,
    a.DATABASE_NAME,
    c.OBJECT_TYPE,
    c.OBJECT_NAME,
    round(SUM(b.DATA_SIZE) / 1024 / 1024) AS DATA_SIZE_MB,
    round(SUM(b.REQUIRED_SIZE) / 1024 / 1024) AS REQUIRED_SIZE_MB
FROM DBA_OB_TABLE_LOCATIONS a
JOIN DBA_OB_TABLET_REPLICAS b
    ON a.TABLET_ID = b.TABLET_ID
    AND a.SVR_IP = b.SVR_IP
    AND a.SVR_PORT = b.SVR_PORT
JOIN DBA_OBJECTS c
    ON a.TABLE_ID = c.OBJECT_ID
WHERE a.DATABASE_NAME != 'oceanbase'
  AND c.OBJECT_TYPE = 'TABLE'
"""

_GROUP_BY_SQL = """
GROUP BY a.SVR_IP, a.SVR_PORT, a.DATABASE_NAME, c.OBJECT_TYPE, c.OBJECT_NAME
"""


class ObTableDataSizeCRUD:
    """OB 租户表大小统计数据层（只读）"""

    def __init__(self, session: Session) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建额外 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("svr_ip"):
                conditions.append("a.SVR_IP LIKE :svr_ip")
                params["svr_ip"] = f"%{search['svr_ip']}%"

            if search.get("database_name"):
                conditions.append("a.DATABASE_NAME LIKE :database_name")
                params["database_name"] = f"%{search['database_name']}%"

            if search.get("object_name"):
                conditions.append("c.OBJECT_NAME LIKE :object_name")
                params["object_name"] = f"%{search['object_name']}%"

        where_clause = f" AND {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    @staticmethod
    def _build_order_clause(order_by: str | None, order_dir: str | None) -> str:
        """根据排序字段和方向构建 ORDER BY 子句，仅允许白名单列"""
        if order_by and order_by.upper() in _ALLOWED_ORDER_COLUMNS:
            direction = "ASC" if order_dir and order_dir.lower() == "asc" else "DESC"
            return f"ORDER BY {order_by.upper()} {direction} NULLS LAST"
        return "ORDER BY REQUIRED_SIZE_MB DESC NULLS LAST"

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询租户表大小统计"""
        where_clause, params = self._build_where_and_params(search)
        order_clause = self._build_order_clause(order_by, order_dir)

        # 动态条件必须插在 GROUP BY 之前
        base_with_where = f"{_BASE_SQL}{where_clause}{_GROUP_BY_SQL}"

        # COUNT 查询（GROUP BY 结果集行数，需包装子查询）
        count_sql = text(f"SELECT COUNT(*) FROM ({base_with_where})")
        count_result = self.db.execute(count_sql, params)
        total = count_result.scalar() or 0

        # DATA 查询（带分页和排序）
        data_sql = text(
            f"{base_with_where} {order_clause} "
            f"OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        )
        data_params = {**params, "offset": offset, "limit": limit}
        data_result = self.db.execute(data_sql, data_params)
        rows = data_result.fetchall()
        columns = data_result.keys()

        return {
            "page_no": (offset // limit) + 1 if limit else 1,
            "page_size": limit,
            "total": total,
            "items": [
                ObTableDataSizeOutSchema(**{k.lower(): v for k, v in zip(columns, row, strict=True)})
                for row in rows
            ],
            "has_next": offset + limit < total,
        }
