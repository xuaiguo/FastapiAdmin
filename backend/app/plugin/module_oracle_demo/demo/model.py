"""
Oracle 示例模型。

继承 OracleBase（不含租户/软删除等框架 Mixin），按需自定义字段。
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.oracle.base_model import OracleBase


class OracleDemoModel(OracleBase):
    """Oracle 示例表"""

    __tablename__: str = "oracle_demo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启用 1:禁用)")
