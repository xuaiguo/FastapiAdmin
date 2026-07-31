"""
OceanBase Oracle 租户示例 CRUD。

所有方法为同步（普通 def），因为 cx_oracle 驱动不支持原生异步。
"""

from app.core.ob_oracle.base_crud import ObOracleCRUDBase

from .model import ObOracleDemoModel
from .schema import ObOracleDemoCreateSchema, ObOracleDemoUpdateSchema


class ObOracleDemoCRUD(ObOracleCRUDBase[ObOracleDemoModel, ObOracleDemoCreateSchema, ObOracleDemoUpdateSchema]):
    """OceanBase Oracle 租户示例数据层"""
    pass
