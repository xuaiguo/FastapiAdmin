"""MySQL 多数据源示例 Service"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException

from .crud import MysqlDemoCRUD
from .model import MysqlDemoModel
from .schema import MysqlDemoCreateSchema, MysqlDemoOutSchema, MysqlDemoUpdateSchema


class MysqlDemoService:
    """MySQL 示例服务层"""

    def __init__(self, mysql_db: AsyncSession) -> None:
        self.db = mysql_db
        self.crud = MysqlDemoCRUD(model=MysqlDemoModel, session=mysql_db)

    async def detail(self, id: int) -> MysqlDemoOutSchema:
        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="数据不存在")
        return MysqlDemoOutSchema.model_validate(obj)

    async def page(self, page_no: int, page_size: int, search: dict | None = None) -> dict:
        offset = (page_no - 1) * page_size
        return await self.crud.page(offset=offset, limit=page_size, search=search)

    async def create(self, data: MysqlDemoCreateSchema) -> MysqlDemoOutSchema:
        obj = await self.crud.create(data=data)
        return MysqlDemoOutSchema.model_validate(obj)

    async def update(self, id: int, data: MysqlDemoUpdateSchema) -> MysqlDemoOutSchema:
        obj = await self.crud.update(id=id, data=data)
        return MysqlDemoOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        await self.crud.delete(ids=ids)
