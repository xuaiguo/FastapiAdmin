"""OB 实时 SQL 审计 CRUD — 查询 V$OB_SQL_AUDIT 视图"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schema import ObSqlAuditOutSchema

# 允许排序的列白名单（防 SQL 注入）
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset({
    "REQUEST_TIME", "REQUEST_MEMORY_MB", "ELAPSED_TIME_MS",
    "EXECUTE_TIME_MS", "TOTAL_WAIT_TIME_MS", "GET_PLAN_TIME_MS",
    "DISK_READS", "AFFECTED_ROWS", "RETURN_ROWS", "PARTITION_CNT",
    "WAIT_TIME_MICRO_MS", "TOTAL_WAITS", "RPC_COUNT", "RET_CODE",
    "NET_TIME_MS", "NET_WAIT_TIME_MS", "QUEUE_TIME_MS", "DECODE_TIME_MS",
    "APPLICATION_WAIT_TIME_MS", "CONCURRENCY_WAIT_TIME_MS",
    "USER_IO_WAIT_TIME_MS", "SCHEDULE_TIME_MS",
    "ROW_CACHE_HIT", "BLOOM_FILTER_CACHE_HIT", "BLOCK_CACHE_HIT",
    "RETRY_CNT", "MEMSTORE_READ_ROW_COUNT", "SSSTORE_READ_ROW_COUNT",
    "EXPECTED_WORKER_COUNT", "USED_WORKER_COUNT",
})

# 固定基础 SQL（单视图查询 + 固定 WHERE 条件）
_BASE_SQL = """
SELECT
    REQUEST_TYPE,
    CONSISTENCY_LEVEL,
    TO_CHAR(TO_TIMESTAMP('1970-01-01 08:00:00','yyyy-mm-dd hh24:mi:ss') + NUMTODSINTERVAL(REQUEST_TIME / 1000000, 'SECOND'), 'yyyy-mm-dd hh24:mi:ss') AS REQUEST_TIME,
    ROUND(REQUEST_MEMORY_USED / 1024 / 1024, 2) AS REQUEST_MEMORY_MB,
    RET_CODE,
    QUERY_SQL,
    SQL_ID,
    STMT_TYPE,
    TENANT_NAME,
    EFFECTIVE_TENANT_ID,
    USER_NAME,
    DB_NAME,
    PLAN_ID,
    ROUND(ELAPSED_TIME / 1000, 2) AS ELAPSED_TIME_MS,
    ROUND(EXECUTE_TIME / 1000, 2) AS EXECUTE_TIME_MS,
    ROUND(TOTAL_WAIT_TIME_MICRO / 1000, 2) AS TOTAL_WAIT_TIME_MS,
    ROUND(GET_PLAN_TIME / 1000, 2) AS GET_PLAN_TIME_MS,
    DISK_READS,
    AFFECTED_ROWS,
    RETURN_ROWS,
    PARTITION_CNT,
    ROUND(WAIT_TIME_MICRO / 1000, 2) AS WAIT_TIME_MICRO_MS,
    EVENT,
    TOTAL_WAITS,
    TRACE_ID,
    RPC_COUNT,
    PLAN_TYPE,
    IS_INNER_SQL,
    IS_EXECUTOR_RPC,
    IS_HIT_PLAN,
    ROUND(NET_TIME / 1000, 2) AS NET_TIME_MS,
    ROUND(NET_WAIT_TIME / 1000, 2) AS NET_WAIT_TIME_MS,
    ROUND(QUEUE_TIME / 1000, 2) AS QUEUE_TIME_MS,
    ROUND(DECODE_TIME / 1000, 2) AS DECODE_TIME_MS,
    ROUND(APPLICATION_WAIT_TIME / 1000, 2) AS APPLICATION_WAIT_TIME_MS,
    ROUND(CONCURRENCY_WAIT_TIME / 1000, 2) AS CONCURRENCY_WAIT_TIME_MS,
    ROUND(USER_IO_WAIT_TIME / 1000, 2) AS USER_IO_WAIT_TIME_MS,
    ROUND(SCHEDULE_TIME / 1000, 2) AS SCHEDULE_TIME_MS,
    ROW_CACHE_HIT,
    BLOOM_FILTER_CACHE_HIT,
    BLOCK_CACHE_HIT,
    RETRY_CNT,
    TABLE_SCAN,
    MEMSTORE_READ_ROW_COUNT,
    SSSTORE_READ_ROW_COUNT,
    EXPECTED_WORKER_COUNT,
    USED_WORKER_COUNT,
    TX_ID,
    SVR_IP,
    CLIENT_IP
FROM V$OB_SQL_AUDIT
WHERE UPPER(USER_NAME) NOT IN ('ROOT', 'SYS')
  AND PLAN_ID != 0
  AND CONSISTENCY_LEVEL > 0
  AND IS_INNER_SQL = 0
  AND STMT_TYPE NOT IN ('NONE', 'VARIABLE_SET', 'CREATE_SAVEPOINT')
  AND IS_EXECUTOR_RPC = 0
"""


class ObSqlAuditCRUD:
    """OB 实时 SQL 审计数据层（只读）"""

    def __init__(self, session: Session) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建额外 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("begin_time"):
                conditions.append(
                    "REQUEST_TIME >= (TO_DATE(:begin_time, 'YYYY-MM-DD HH24:MI:SS') "
                    "- TO_DATE('1970-01-01 08:00:00', 'YYYY-MM-DD HH24:MI:SS')) * 86400000000"
                )
                params["begin_time"] = search["begin_time"]

            if search.get("end_time"):
                conditions.append(
                    "REQUEST_TIME <= (TO_DATE(:end_time, 'YYYY-MM-DD HH24:MI:SS') "
                    "- TO_DATE('1970-01-01 08:00:00', 'YYYY-MM-DD HH24:MI:SS')) * 86400000000"
                )
                params["end_time"] = search["end_time"]

            if search.get("trace_id"):
                conditions.append("TRACE_ID = :trace_id")
                params["trace_id"] = search["trace_id"]

            if search.get("sql_id"):
                conditions.append("SQL_ID = :sql_id")
                params["sql_id"] = search["sql_id"]

            if search.get("ret_code_min") is not None:
                conditions.append("RET_CODE >= :ret_code_min")
                params["ret_code_min"] = search["ret_code_min"]

            if search.get("ret_code_max") is not None:
                conditions.append("RET_CODE <= :ret_code_max")
                params["ret_code_max"] = search["ret_code_max"]

            if search.get("memory_min") is not None:
                conditions.append("ROUND(REQUEST_MEMORY_USED / 1024 / 1024, 2) >= :memory_min")
                params["memory_min"] = search["memory_min"]

            if search.get("memory_max") is not None:
                conditions.append("ROUND(REQUEST_MEMORY_USED / 1024 / 1024, 2) <= :memory_max")
                params["memory_max"] = search["memory_max"]

        where_clause = f" AND {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    @staticmethod
    def _build_order_clause(order_by: str | None, order_dir: str | None) -> str:
        """根据排序字段和方向构建 ORDER BY 子句，仅允许白名单列"""
        if order_by and order_by.upper() in _ALLOWED_ORDER_COLUMNS:
            direction = "ASC" if order_dir and order_dir.lower() == "asc" else "DESC"
            return f"ORDER BY {order_by.upper()} {direction} NULLS LAST"
        return "ORDER BY REQUEST_TIME DESC NULLS LAST"

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询 SQL 审计"""
        where_clause, params = self._build_where_and_params(search)
        order_clause = self._build_order_clause(order_by, order_dir)

        # COUNT 查询
        count_sql = text(f"SELECT COUNT(*) FROM ({_BASE_SQL}{where_clause})")
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
                ObSqlAuditOutSchema(**{k.lower(): v for k, v in zip(columns, row, strict=True)})
                for row in rows
            ],
            "has_next": offset + limit < total,
        }
