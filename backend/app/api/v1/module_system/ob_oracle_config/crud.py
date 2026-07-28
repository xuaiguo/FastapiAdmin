"""OceanBase Oracle 配置 CRUD"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import ObOracleConfigModel
from .schema import ObOracleConfigCreateSchema, ObOracleConfigUpdateSchema


class ObOracleConfigCRUD(CRUDBase[ObOracleConfigModel, ObOracleConfigCreateSchema, ObOracleConfigUpdateSchema]):
    """OceanBase Oracle 配置数据层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(ObOracleConfigModel, auth, db)
