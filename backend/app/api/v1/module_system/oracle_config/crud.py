"""Oracle 配置 CRUD"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import OracleConfigModel
from .schema import OracleConfigCreateSchema, OracleConfigUpdateSchema


class OracleConfigCRUD(CRUDBase[OracleConfigModel, OracleConfigCreateSchema, OracleConfigUpdateSchema]):
    """Oracle 配置数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(OracleConfigModel, auth, db)
