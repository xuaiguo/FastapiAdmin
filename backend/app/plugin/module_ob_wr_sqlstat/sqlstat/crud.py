"""OB SQL 性能统计 CRUD — 查询 DBA_WR_SQLSTAT 视图"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schema import ObWrSqlstatOutSchema

# 允许排序的列白名单（防 SQL 注入）
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset({
    "BEGIN_INTERVAL_TIME", "END_INTERVAL_TIME",
    "ELAPSED_TIME_DELTA_MS", "ELAPSED_TIME_DELTA_MS_PER_EXEC",
    "EXECUTIONS_DELTA", "CPU_TIME_DELTA_MS",
    "DISK_READS_DELTA", "BUFFER_GETS_DELTA",
    "CCWAIT_DELTA_MS", "USERIO_WAIT_DELTA_MS", "APWAIT_DELTA_MS",
    "PHYSICAL_READ_REQUESTS_DELTA", "PHYSICAL_READ_BYTES_DELTA",
    "WRITE_THROTTLE_DELTA", "ROWS_PROCESSED_DELTA",
    "FETCHES_DELTA", "RETRY_DELTA",
})

# COUNT 专用 SQL（不含 DBA_WR_SQLTEXT JOIN，提升统计效率）
_COUNT_SQL = """
SELECT COUNT(*)
FROM DBA_WR_SNAPSHOT a
JOIN DBA_WR_SQLSTAT b ON a.SNAP_ID = b.SNAP_ID
WHERE b.PARSING_DB_NAME NOT IN ('oceanbase', 'SYS')
"""

# 固定基础 SQL（3 表 JOIN + 固定过滤条件）
_BASE_SQL = """
SELECT
    to_char(a.BEGIN_INTERVAL_TIME, 'yyyy-mm-dd hh24:mi:ss') AS BEGIN_INTERVAL_TIME,
    to_char(a.END_INTERVAL_TIME, 'yyyy-mm-dd hh24:mi:ss') AS END_INTERVAL_TIME,
    b.SQL_ID,
    c.QUERY_SQL,
    b.PARSING_DB_NAME,
    round(b.ELAPSED_TIME_DELTA / 1000, 2) AS ELAPSED_TIME_DELTA_MS,
    round(b.ELAPSED_TIME_DELTA / decode(nvl(b.EXECUTIONS_DELTA, 0), 0, 1, b.EXECUTIONS_DELTA) / 1000, 2) AS ELAPSED_TIME_DELTA_MS_PER_EXEC,
    b.EXECUTIONS_DELTA,
    round(b.CPU_TIME_DELTA / 1000, 2) AS CPU_TIME_DELTA_MS,
    b.DISK_READS_DELTA,
    b.BUFFER_GETS_DELTA,
    round(b.CCWAIT_DELTA / 1000, 2) AS CCWAIT_DELTA_MS,
    round(b.USERIO_WAIT_DELTA / 1000, 2) AS USERIO_WAIT_DELTA_MS,
    round(b.APWAIT_DELTA / 1000, 2) AS APWAIT_DELTA_MS,
    b.PHYSICAL_READ_REQUESTS_DELTA,
    b.PHYSICAL_READ_BYTES_DELTA,
    b.WRITE_THROTTLE_DELTA,
    b.ROWS_PROCESSED_DELTA,
    b.MEMSTORE_READ_ROWS_DELTA,
    b.MINOR_SSSTORE_READ_ROWS_DELTA,
    b.MAJOR_SSSTORE_READ_ROWS_DELTA,
    b.RPC_DELTA,
    b.FETCHES_DELTA,
    b.RETRY_DELTA,
    b.PARTITION_DELTA,
    b.NESTED_SQL_DELTA,
    b.ROUTE_MISS_DELTA,
    c.SQL_TYPE,
    b.PLAN_HASH,
    b.PLAN_TYPE,
    a.SNAP_ID,
    b.SOURCE_IP,
    b.MODULE,
    b.ACTION
FROM DBA_WR_SNAPSHOT a
JOIN DBA_WR_SQLSTAT b ON a.SNAP_ID = b.SNAP_ID
LEFT JOIN DBA_WR_SQLTEXT c ON b.SNAP_ID = c.SNAP_ID AND b.SQL_ID = c.SQL_ID AND c.SQL_TYPE <= 6
WHERE b.PARSING_DB_NAME NOT IN ('oceanbase', 'SYS')
"""


class ObWrSqlstatCRUD:
    """OB SQL 性能统计数据层（只读）"""

    def __init__(self, session: Session) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建额外 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("begin_time"):
                conditions.append("a.END_INTERVAL_TIME >= to_date(:begin_time, 'yyyy-mm-dd hh24:mi:ss')")
                params["begin_time"] = search["begin_time"]

            if search.get("end_time"):
                conditions.append("a.BEGIN_INTERVAL_TIME <= to_date(:end_time, 'yyyy-mm-dd hh24:mi:ss')")
                params["end_time"] = search["end_time"]

            if search.get("parsing_db_name"):
                conditions.append("b.PARSING_DB_NAME = :parsing_db_name")
                params["parsing_db_name"] = search["parsing_db_name"]

            if search.get("sql_id"):
                conditions.append("b.SQL_ID LIKE :sql_id")
                params["sql_id"] = f"%{search['sql_id']}%"

        where_clause = f" AND {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    @staticmethod
    def _build_order_clause(order_by: str | None, order_dir: str | None) -> str:
        """根据排序字段和方向构建 ORDER BY 子句，仅允许白名单列"""
        if order_by and order_by.upper() in _ALLOWED_ORDER_COLUMNS:
            direction = "ASC" if order_dir and order_dir.lower() == "asc" else "DESC"
            return f"ORDER BY {order_by.upper()} {direction} NULLS LAST"
        return "ORDER BY END_INTERVAL_TIME DESC NULLS LAST"

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询 SQL 性能统计"""
        where_clause, params = self._build_where_and_params(search)
        order_clause = self._build_order_clause(order_by, order_dir)

        # COUNT 查询（使用不含 SQLTEXT JOIN 的精简 SQL）
        count_sql = text(f"{_COUNT_SQL}{where_clause}")
        count_result = self.db.execute(count_sql, params)
        total = count_result.scalar() or 0

        # DATA 查询（带分页和排序）
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
                ObWrSqlstatOutSchema(**{k.lower(): v for k, v in zip(columns, row, strict=True)})
                for row in rows
            ],
            "has_next": offset + limit < total,
        }
