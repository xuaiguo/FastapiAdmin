"""Oracle 示例 Service"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException

from .crud import OracleDemoCRUD
from .model import OracleDemoModel
from .schema import OracleDemoCreateSchema, OracleDemoOutSchema, OracleDemoUpdateSchema


class OracleDemoService:
    """Oracle 示例服务层"""

    def __init__(self, oracle_db: AsyncSession) -> None:
        self.db = oracle_db
        self.crud = OracleDemoCRUD(model=OracleDemoModel, session=oracle_db)

    async def detail(self, id: int) -> OracleDemoOutSchema:
        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="数据不存在")
        return OracleDemoOutSchema.model_validate(obj)

    async def page(self, page_no: int, page_size: int, search: dict | None = None) -> dict:
        offset = (page_no - 1) * page_size
        return await self.crud.page(offset=offset, limit=page_size, search=search)

    async def create(self, data: OracleDemoCreateSchema) -> OracleDemoOutSchema:
        obj = await self.crud.create(data=data)
        return OracleDemoOutSchema.model_validate(obj)

    async def update(self, id: int, data: OracleDemoUpdateSchema) -> OracleDemoOutSchema:
        obj = await self.crud.update(id=id, data=data)
        return OracleDemoOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        await self.crud.delete(ids=ids)
