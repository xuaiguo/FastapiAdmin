"""
OceanBase Oracle 租户示例模型。

继承 ObOracleBase（不含租户/软删除等框架 Mixin），按需自定义字段。
参考此代码再做一套支持oceanbase的oracle租户的多数据源功能。
"""

from sqlalchemy import Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ob_oracle.base_model import ObOracleBase

# OceanBase Oracle 序列名约定：表名 + _seq
OB_ORACLE_DEMO_SEQ = Sequence("ob_oracle_demo_seq", start=1, increment=1)


class ObOracleDemoModel(ObOracleBase):
    """OceanBase Oracle 租户示例表"""

    __tablename__: str = "ob_oracle_demo"

    id: Mapped[int] = mapped_column(Integer, OB_ORACLE_DEMO_SEQ, primary_key=True, comment="主键ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启用 1:禁用)")
