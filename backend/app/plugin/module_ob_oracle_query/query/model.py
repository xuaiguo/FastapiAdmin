"""OB Oracle SQL 查询历史模型"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class QueryHistoryModel(ModelMixin, UserMixin):
    """SQL 查询历史记录表"""

    __tablename__: str = "ob_oracle_query_history"
    __table_args__: dict[str, str] = {"comment": "OB Oracle SQL 查询历史"}

    config_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="数据源配置ID")
    config_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="数据源名称")
    sql: Mapped[str] = mapped_column(Text, nullable=False, comment="SQL语句")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="执行状态(0:成功 1:失败)")
    elapsed_ms: Mapped[float | None] = mapped_column(nullable=True, comment="执行耗时(ms)")
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="返回行数")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
