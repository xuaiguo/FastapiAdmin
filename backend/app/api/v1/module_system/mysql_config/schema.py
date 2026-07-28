"""MySQL 配置 Schema"""

from dataclasses import dataclass

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema


# 密码脱敏占位符，前端提交此值表示密码未修改
PASSWORD_MASK = "****"


class MysqlConfigCreateSchema(BaseModel):
    """新增 MySQL 配置"""

    name: str = Field(..., description="实例名称")
    host: str = Field(..., description="主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="端口")
    database_name: str = Field(..., description="数据库名")
    db_model: str = Field(default="local", description="数据源模式(local/cloud/oceanbase)")
    charset: str = Field(default="utf8mb4", description="字符集")
    username: str = Field(..., description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    pool_size: int = Field(default=5, ge=1, le=100, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, le=200, description="最大溢出连接数")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启用 1:禁用)")
    remark: str | None = Field(default=None, max_length=500, description="备注")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("实例名称不能为空")
        return v

    @field_validator("db_model")
    @classmethod
    def validate_db_model(cls, v: str) -> str:
        if v not in ("local", "cloud", "oceanbase"):
            raise ValueError("数据源模式只能是 local、cloud 或 oceanbase")
        return v


class MysqlConfigUpdateSchema(MysqlConfigCreateSchema):
    """更新 MySQL 配置"""


class MysqlConfigOutSchema(MysqlConfigCreateSchema, BaseSchema, UserBySchema):
    """响应模型（密码脱敏）"""

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("password")
    @classmethod
    def serialize_password(cls, _v: str) -> str:
        """密码字段始终返回脱敏值，防止密文泄露到前端导致二次加密"""
        return PASSWORD_MASK


@dataclass
class MysqlConfigQueryParam:
    """查询参数"""

    name: str | None = Query(None, description="实例名称")
    host: str | None = Query(None, description="主机地址")
    db_model: str | None = Query(None, description="数据源模式(local/cloud/oceanbase)")
    status: int | None = Query(None, description="状态")
    created_id: int | None = Query(None, description="创建人")
    updated_id: int | None = Query(None, description="更新人")
    created_time: list | None = Query(None, description="创建时间范围")
    updated_time: list | None = Query(None, description="更新时间范围")

    def __post_init__(self) -> None:
        if self.name:
            self.name = (QueueEnum.like.value, self.name)
        if self.host:
            self.host = (QueueEnum.like.value, self.host)
        if self.db_model:
            self.db_model = (QueueEnum.eq.value, self.db_model)
        if isinstance(self.status, int):
            self.status = (QueueEnum.eq.value, self.status)
