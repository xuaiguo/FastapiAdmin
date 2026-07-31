"""OB JOBS 查询 Service"""

from typing import Any

from sqlalchemy.orm import Session

from .crud import ObSchedulerJobsCRUD


class ObSchedulerJobsService:
    """OB JOBS 查询服务"""

    def __init__(self, ob_db: Session) -> None:
        self.crud = ObSchedulerJobsCRUD(session=ob_db)

    def page(
        self,
        page_no: int,
        page_size: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询调度任务"""
        offset = (page_no - 1) * page_size
        return self.crud.page(
            offset=offset,
            limit=page_size,
            search=search,
            order_by=order_by,
            order_dir=order_dir,
        )
