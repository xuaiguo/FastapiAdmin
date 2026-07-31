"""OB Oracle SQL 查询历史 CRUD"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import QueryHistoryModel
from .schema import QueryHistoryCreateSchema, QueryHistoryUpdateSchema


class QueryHistoryCRUD(CRUDBase[QueryHistoryModel, QueryHistoryCreateSchema, QueryHistoryUpdateSchema]):
    """SQL 查询历史 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(QueryHistoryModel, auth, db)
