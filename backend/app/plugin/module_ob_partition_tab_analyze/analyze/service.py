"""OB 分区表分析 Service"""

from typing import Any

from sqlalchemy.orm import Session

from .crud import ObPartitionTabAnalyzeCRUD


class ObPartitionTabAnalyzeService:
    """OB 分区表分析服务"""

    def __init__(self, ob_db: Session) -> None:
        self.crud = ObPartitionTabAnalyzeCRUD(session=ob_db)

    def page(
        self,
        page_no: int,
        page_size: int,
        search: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """分页查询分区表分析"""
        offset = (page_no - 1) * page_size
        return self.crud.page(
            offset=offset,
            limit=page_size,
            search=search,
        )
