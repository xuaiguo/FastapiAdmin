"""OB JOBS 查询 CRUD — 查询 dba_scheduler_jobs 视图"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schema import ObSchedulerJobsOutSchema

# 允许排序的列白名单
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset({
    "JOB_NAME", "JOB_ACTION", "LAST_START_DATE", "NEXT_RUN_DATE",
    "PROGRAM_NAME", "SCHEDULE_NAME", "ENABLED", "STATE",
})

# 基础 SQL
_BASE_SQL = """
SELECT
    OWNER,
    JOB_NAME,
    JOB_STYLE,
    JOB_TYPE,
    JOB_CLASS,
    JOB_ACTION,
    REPEAT_INTERVAL,
    TO_CHAR(LAST_START_DATE, 'yyyy-mm-dd hh24:mi:ss') AS LAST_START_DATE,
    TO_CHAR(NEXT_RUN_DATE, 'yyyy-mm-dd hh24:mi:ss') AS NEXT_RUN_DATE,
    PROGRAM_NAME,
    SCHEDULE_NAME,
    ENABLED,
    STATE,
    COMMENTS,
    MAX_RUN_DURATION
FROM dba_scheduler_jobs
WHERE 1=1
"""


class ObSchedulerJobsCRUD:
    """OB JOBS 查询数据层（只读）"""

    def __init__(self, session: Session) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建额外 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("owner"):
                conditions.append("OWNER LIKE :owner")
                params["owner"] = f"%{search['owner']}%"

            if search.get("job_name"):
                conditions.append("JOB_NAME LIKE :job_name")
                params["job_name"] = f"%{search['job_name']}%"

            if search.get("job_action"):
                conditions.append("JOB_ACTION LIKE :job_action")
                params["job_action"] = f"%{search['job_action']}%"

        where_clause = f" AND {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    @staticmethod
    def _build_order_clause(order_by: str | None, order_dir: str | None) -> str:
        """根据排序字段和方向构建 ORDER BY 子句"""
        if order_by and order_by.upper() in _ALLOWED_ORDER_COLUMNS:
            direction = "ASC" if order_dir and order_dir.lower() == "asc" else "DESC"
            return f"ORDER BY {order_by.upper()} {direction} NULLS LAST"
        return "ORDER BY JOB_NAME ASC NULLS LAST"

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询调度任务"""
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
                ObSchedulerJobsOutSchema(**{k.lower(): v for k, v in zip(columns, row, strict=True)})
                for row in rows
            ],
            "has_next": offset + limit < total,
        }
