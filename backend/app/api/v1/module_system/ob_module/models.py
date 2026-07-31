"""OB 模块管理相关数据模型

Note: OB 模块管理是全局管理功能，配置全局共享。
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import MappedBase as Base


class ObModuleParentMenu(Base):
    """OB 模块父菜单配置表"""

    __tablename__ = "sys_ob_module_parent_menu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_menu.id", ondelete="CASCADE"), unique=True, comment="父菜单ID"
    )
    menu_name: Mapped[str] = mapped_column(String(100), comment="父菜单名称")
    created_time: Mapped[datetime | None] = mapped_column(server_default=func.now(), comment="创建时间")

    menu = relationship("MenuModel", backref="ob_module_parent_configs")


class ObModule(Base):
    """OB 模块管理表（手动添加的模块）"""

    __tablename__ = "sys_ob_module"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_name: Mapped[str] = mapped_column(String(100), unique=True, comment="模块名称（如 ObOracleQuery）")
    module_label: Mapped[str] = mapped_column(String(100), comment="模块显示名称（如 SQL查询）")
    source_type: Mapped[int] = mapped_column(Integer, default=2, comment="来源类型：2=手动添加")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="状态：0=启用 1=禁用")
    created_time: Mapped[datetime | None] = mapped_column(server_default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(server_default=func.now(), onupdate=func.now(), comment="更新时间")


class ObOracleConfigModule(Base):
    """数据源与模块关联表"""

    __tablename__ = "sys_ob_oracle_config_module"
    __table_args__ = (
        UniqueConstraint("config_id", "module_name", name="uk_config_module"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_ob_oracle_config.id", ondelete="CASCADE"), comment="数据源配置ID"
    )
    module_name: Mapped[str] = mapped_column(String(100), comment="模块名称")
    created_time: Mapped[datetime | None] = mapped_column(server_default=func.now(), comment="创建时间")

    config = relationship("ObOracleConfigModel", backref="module_configs")


class ObOracleConfigUser(Base):
    """数据源与用户关联表"""

    __tablename__ = "sys_ob_oracle_config_user"
    __table_args__ = (
        UniqueConstraint("config_id", "user_id", name="uk_config_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_ob_oracle_config.id", ondelete="CASCADE"), comment="数据源配置ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), comment="用户ID"
    )
    created_time: Mapped[datetime | None] = mapped_column(server_default=func.now(), comment="创建时间")

    config = relationship("ObOracleConfigModel", backref="user_configs")
    user = relationship("UserModel", backref="ob_oracle_configs")
