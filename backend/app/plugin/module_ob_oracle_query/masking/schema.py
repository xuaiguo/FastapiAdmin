"""敏感字段脱敏 — Schema"""

import re

from pydantic import BaseModel, Field, field_validator


# ===== 脱敏规则 =====

class DataMaskingRuleCreateSchema(BaseModel):
    rule_type: int = Field(..., description="规则类型编号")
    rule_regex: str = Field(..., max_length=255, description="正则表达式（必须分组）")
    hide_group: int = Field(default=2, ge=1, description="隐藏分组序号")
    rule_desc: str = Field(default="", max_length=200, description="规则描述")

    @field_validator("rule_regex")
    @classmethod
    def validate_regex(cls, v: str) -> str:
        try:
            compiled = re.compile(v)
            if compiled.groups == 0:
                raise ValueError("正则表达式必须包含至少一个捕获分组")
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        return v


class DataMaskingRuleUpdateSchema(BaseModel):
    rule_regex: str | None = Field(None, max_length=255)
    hide_group: int | None = Field(None, ge=1)
    rule_desc: str | None = Field(None, max_length=200)

    @field_validator("rule_regex")
    @classmethod
    def validate_regex(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            compiled = re.compile(v)
            if compiled.groups == 0:
                raise ValueError("正则表达式必须包含至少一个捕获分组")
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        return v


class DataMaskingRuleOutSchema(BaseModel):
    id: int
    rule_type: int
    rule_regex: str
    hide_group: int
    rule_desc: str
    created_time: str | None = None
    updated_time: str | None = None

    model_config = {"from_attributes": True}


# ===== 脱敏字段配置 =====

class DataMaskingColumnCreateSchema(BaseModel):
    config_id: int = Field(..., description="数据源配置ID")
    table_schema: str = Field(default="*", max_length=64, description="库/Schema名")
    table_name: str = Field(default="*", max_length=64, description="表名")
    column_name: str = Field(..., max_length=64, description="列名")
    rule_type: int = Field(..., description="关联脱敏规则类型")
    active: bool = Field(default=True, description="是否激活")


class DataMaskingColumnUpdateSchema(BaseModel):
    table_schema: str | None = None
    table_name: str | None = None
    column_name: str | None = None
    rule_type: int | None = None
    active: bool | None = None


class DataMaskingColumnOutSchema(BaseModel):
    id: int
    config_id: int
    table_schema: str
    table_name: str
    column_name: str
    rule_type: int
    active: bool
    created_time: str | None = None
    updated_time: str | None = None

    model_config = {"from_attributes": True}


class DataMaskingColumnQueryParam(BaseModel):
    """脱敏字段配置搜索参数"""
    config_id: int | None = Field(None, description="数据源ID")
    active: bool | None = Field(None, description="激活状态")
