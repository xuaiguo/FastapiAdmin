"""Oracle 示例 CRUD"""

from app.core.oracle.base_crud import OracleCRUDBase

from .model import OracleDemoModel
from .schema import OracleDemoCreateSchema, OracleDemoUpdateSchema


class OracleDemoCRUD(OracleCRUDBase[OracleDemoModel, OracleDemoCreateSchema, OracleDemoUpdateSchema]):
    """Oracle 示例数据层"""
    pass
