"""Oracle 表空间查询 Service"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .crud import OracleTablespaceCRUD


class OracleTablespaceService:
    """Oracle 表空间查询服务"""

    def __init__(self, oracle_db: AsyncSession) -> None:
        self.crud = OracleTablespaceCRUD(session=oracle_db)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> dict[str, Any]:
        """分页查询表空间"""
        offset = (page_no - 1) * page_size
        return await self.crud.page(
            offset=offset, limit=page_size, search=search,
            order_by=order_by, order_dir=order_dir,
        )
