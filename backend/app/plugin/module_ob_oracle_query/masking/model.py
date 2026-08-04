"""敏感字段脱敏 — 数据模型"""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class DataMaskingRuleModel(ModelMixin):
    """脱敏规则表

    定义正则表达式和隐藏组，用于对查询结果中的敏感字段进行脱敏处理。
    正则必须包含捕获分组，hide_group 指定用 **** 替换第几个分组。
    """

    __tablename__: str = "sys_data_masking_rule"
    __table_args__: dict[str, str] = {"comment": "敏感字段脱敏规则"}

    rule_type: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, comment="规则类型编号")
    rule_regex: Mapped[str] = mapped_column(String(255), nullable=False, comment="正则表达式（必须分组）")
    hide_group: Mapped[int] = mapped_column(Integer, nullable=False, default=2, comment="需要隐藏的分组序号（从1开始）")
    rule_desc: Mapped[str] = mapped_column(String(200), nullable=False, default="", comment="规则描述")


class DataMaskingColumnModel(ModelMixin):
    """脱敏字段配置表

    按数据源+表+列名配置哪些字段需要脱敏，以及使用哪种脱敏规则。
    table_schema / table_name 设为 "*" 表示通配所有。
    """

    __tablename__: str = "sys_data_masking_column"
    __table_args__: dict[str, str] = {"comment": "脱敏字段配置"}

    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_ob_oracle_config.id", ondelete="CASCADE"), nullable=False, comment="数据源配置ID"
    )
    table_schema: Mapped[str] = mapped_column(String(64), nullable=False, default="*", comment="库/Schema名（*=所有）")
    table_name: Mapped[str] = mapped_column(String(64), nullable=False, default="*", comment="表名（*=所有）")
    column_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="列名")
    rule_type: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_data_masking_rule.rule_type", ondelete="CASCADE"), nullable=False, comment="关联脱敏规则类型"
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否激活")
