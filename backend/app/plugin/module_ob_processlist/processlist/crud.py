"""OB ProcessList 查询 CRUD — 查询 gv$ob_processlist 视图"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schema import ObProcesslistOutSchema

# 允许排序的列白名单（USER 和 TIME 是 Oracle 保留字，需双引号）
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset({
    "SVR_IP", '"USER"', "HOST", "COMMAND", '"TIME"', "TOTAL_TIME",
    "STATE", "USER_CLIENT_IP", "USER_HOST", "SQL_ID", "TRACE_ID", "MODULE",
})

# 基础 SQL
_BASE_SQL = """
SELECT
    a.ID,
    a.SVR_IP,
    a."USER",
    a.HOST,
    a.DB,
    a.TENANT,
    a.COMMAND,
    a."TIME",
    a.TOTAL_TIME,
    a.STATE,
    a.INFO,
    a.USER_CLIENT_IP,
    a.USER_HOST,
    a.SQL_ID,
    a.TRANS_ID,
    a.TRACE_ID,
    a.TOP_TRACE_ID,
    a.MODULE,
    a.ACTION,
    a.CLIENT_INFO
FROM gv$ob_processlist a
WHERE 1=1
"""


class ObProcesslistCRUD:
    """OB ProcessList 查询数据层（只读）"""

    def __init__(self, session: Session) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建额外 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("user"):
                conditions.append('a."USER" LIKE :user')
                params["user"] = f"%{search['user']}%"

            if search.get("db"):
                conditions.append("a.DB LIKE :db")
                params["db"] = f"%{search['db']}%"

            if search.get("state"):
                conditions.append("UPPER(a.STATE) = UPPER(:state)")
                params["state"] = search["state"]

            if search.get("info"):
                conditions.append("a.INFO LIKE :info")
                params["info"] = f"%{search['info']}%"

            if search.get("user_client_ip"):
                conditions.append("a.USER_CLIENT_IP LIKE :user_client_ip")
                params["user_client_ip"] = f"%{search['user_client_ip']}%"

            if search.get("sql_id"):
                conditions.append("UPPER(a.SQL_ID) LIKE UPPER(:sql_id)")
                params["sql_id"] = f"%{search['sql_id']}%"

            if search.get("trace_id"):
                conditions.append("a.TRACE_ID LIKE :trace_id")
                params["trace_id"] = f"%{search['trace_id']}%"

        where_clause = f" AND {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    @staticmethod
    def _build_order_clause(order_by: str | None, order_dir: str | None) -> str:
        """根据排序字段和方向构建 ORDER BY 子句"""
        if order_by:
            upper = order_by.upper()
            sort_col = f'"{upper}"' if upper in ("USER", "TIME") else upper
            if sort_col in _ALLOWED_ORDER_COLUMNS:
                direction = "ASC" if order_dir and order_dir.lower() == "asc" else "DESC"
                return f"ORDER BY {sort_col} {direction} NULLS LAST"
        return 'ORDER BY a."TIME" DESC NULLS LAST'

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询 ProcessList"""
        where_clause, params = self._build_where_and_params(search)
        order_clause = self._build_order_clause(order_by, order_dir)

        # COUNT 查询
        count_sql = text(f"SELECT COUNT(*) FROM ({_BASE_SQL}{where_clause})")
        count_result = self.db.execute(count_sql, params)
        total = count_result.scalar() or 0

        # DATA 查询
        data_sql = text(
            f"{_BASE_SQL}{where_clause} {order_clause} "
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
                ObProcesslistOutSchema(**{k.lower(): v for k, v in zip(columns, row, strict=True)})
                for row in rows
            ],
            "has_next": offset + limit < total,
        }
