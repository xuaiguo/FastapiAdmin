"""敏感字段脱敏 — CRUD"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import DataMaskingColumnModel, DataMaskingRuleModel
from .schema import (
    DataMaskingColumnCreateSchema,
    DataMaskingColumnUpdateSchema,
    DataMaskingRuleCreateSchema,
    DataMaskingRuleUpdateSchema,
)


class DataMaskingRuleCRUD(CRUDBase[DataMaskingRuleModel, DataMaskingRuleCreateSchema, DataMaskingRuleUpdateSchema]):
    """脱敏规则 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(DataMaskingRuleModel, auth, db)


class DataMaskingColumnCRUD(CRUDBase[DataMaskingColumnModel, DataMaskingColumnCreateSchema, DataMaskingColumnUpdateSchema]):
    """脱敏字段配置 CRUD"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(DataMaskingColumnModel, auth, db)
