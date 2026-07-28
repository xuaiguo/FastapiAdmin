"""
OceanBase Oracle 租户模型基类。

精简基类，不含 FastapiAdmin 框架特有的 Mixin（租户隔离/软删除/审计字段）。
OceanBase 业务模型直接继承此类，按需自定义字段。
"""

from sqlalchemy.orm import DeclarativeBase


class ObOracleBase(DeclarativeBase):
    """
    OceanBase Oracle 租户模型基类。

    与 base_model.py 中的 MappedBase 不同:
    - 不含 ModelMixin（无 is_deleted / created_time / updated_time）
    - 不含 TenantMixin（无 tenant_id）
    - 不含 UserMixin（无 created_id / updated_id）

    OceanBase 业务表通常有自己独立的字段规范，由具体模块自行定义。
    """

    __abstract__: bool = True
