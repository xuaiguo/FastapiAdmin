"""MySQL 数据库连接配置模型"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class MysqlConfigModel(ModelMixin):
    """MySQL 数据库连接配置表"""

    __tablename__: str = "sys_mysql_config"
    __table_args__: dict[str, str] = {"comment": "MySQL 数据库连接配置"}
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by"]

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="实例名称")
    host: Mapped[str] = mapped_column(String(200), nullable=False, comment="主机地址")
    port: Mapped[int] = mapped_column(Integer, default=3306, nullable=False, comment="端口")
    database_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="数据库名")
    db_model: Mapped[str] = mapped_column(String(20), default="local", nullable=False, comment="数据源模式(local/cloud/oceanbase)")
    charset: Mapped[str] = mapped_column(String(20), default="utf8mb4", nullable=False, comment="字符集")
    username: Mapped[str] = mapped_column(String(100), nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(500), nullable=False, comment="密码")
    pool_size: Mapped[int] = mapped_column(Integer, default=5, nullable=False, comment="连接池大小")
    max_overflow: Mapped[int] = mapped_column(Integer, default=10, nullable=False, comment="最大溢出连接数")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0:启用 1:禁用)", index=True)
    remark: Mapped[str | None] = mapped_column(String(500), default=None, nullable=True, comment="备注")
