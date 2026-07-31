"""MySQL 配置 CRUD"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import MysqlConfigModel
from .schema import MysqlConfigCreateSchema, MysqlConfigUpdateSchema


class MysqlConfigCRUD(CRUDBase[MysqlConfigModel, MysqlConfigCreateSchema, MysqlConfigUpdateSchema]):
    """MySQL 配置数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(MysqlConfigModel, auth, db)
