"""
OceanBase Oracle 租户示例 Service。

所有方法为同步（普通 def），因为 cx_oracle 驱动不支持原生异步。
Controller 层通过 asyncio.to_thread() 调用这些同步方法。
"""

from sqlalchemy.orm import Session

from app.core.exceptions import CustomException

from .crud import ObOracleDemoCRUD
from .model import ObOracleDemoModel
from .schema import ObOracleDemoCreateSchema, ObOracleDemoOutSchema, ObOracleDemoUpdateSchema


class ObOracleDemoService:
    """OceanBase Oracle 租户示例服务层"""

    def __init__(self, ob_db: Session) -> None:
        self.db = ob_db
        self.crud = ObOracleDemoCRUD(model=ObOracleDemoModel, session=ob_db)

    def detail(self, id: int) -> ObOracleDemoOutSchema:
        obj = self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="数据不存在")
        return ObOracleDemoOutSchema.model_validate(obj)

    def page(self, page_no: int, page_size: int, search: dict | None = None) -> dict:
        offset = (page_no - 1) * page_size
        return self.crud.page(offset=offset, limit=page_size, search=search)

    def create(self, data: ObOracleDemoCreateSchema) -> ObOracleDemoOutSchema:
        obj = self.crud.create(data=data)
        return ObOracleDemoOutSchema.model_validate(obj)

    def update(self, id: int, data: ObOracleDemoUpdateSchema) -> ObOracleDemoOutSchema:
        obj = self.crud.update(id=id, data=data)
        return ObOracleDemoOutSchema.model_validate(obj)

    def delete(self, ids: list[int]) -> None:
        self.crud.delete(ids=ids)
