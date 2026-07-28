"""Oracle 配置 Schema"""

from dataclasses import dataclass

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema


# 密码脱敏占位符，前端提交此值表示密码未修改
PASSWORD_MASK = "****"


class OracleConfigCreateSchema(BaseModel):
    """新增 Oracle 配置"""

    name: str = Field(..., description="实例名称")
    host: str = Field(..., description="主机地址")
    port: int = Field(default=1521, ge=1, le=65535, description="端口")
    service_name: str = Field(..., description="Oracle Service Name")
    db_type: str = Field(default="CDB", description="数据库类型(CDB/PDB)")
    auth_mode: str = Field(default="NORMAL", description="连接身份(NORMAL/SYSDBA/SYSOPER)")
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

    @field_validator("db_type")
    @classmethod
    def validate_db_type(cls, v: str) -> str:
        if v not in ("CDB", "PDB"):
            raise ValueError("数据库类型只能是 CDB 或 PDB")
        return v

    @field_validator("auth_mode")
    @classmethod
    def validate_auth_mode(cls, v: str) -> str:
        if v not in ("NORMAL", "SYSDBA", "SYSOPER"):
            raise ValueError("连接身份只能是 NORMAL、SYSDBA 或 SYSOPER")
        return v


class OracleConfigUpdateSchema(OracleConfigCreateSchema):
    """更新 Oracle 配置"""


class OracleConfigOutSchema(OracleConfigCreateSchema, BaseSchema, UserBySchema):
    """响应模型（密码脱敏）"""

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("password")
    @classmethod
    def serialize_password(cls, _v: str) -> str:
        """密码字段始终返回脱敏值，防止密文泄露到前端导致二次加密"""
        return PASSWORD_MASK


@dataclass
class OracleConfigQueryParam:
    """查询参数"""

    name: str | None = Query(None, description="实例名称")
    host: str | None = Query(None, description="主机地址")
    db_type: str | None = Query(None, description="数据库类型(CDB/PDB)")
    auth_mode: str | None = Query(None, description="连接身份(NORMAL/SYSDBA/SYSOPER)")
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
        if self.db_type:
            self.db_type = (QueueEnum.eq.value, self.db_type)
        if self.auth_mode:
            self.auth_mode = (QueueEnum.eq.value, self.auth_mode)
        if isinstance(self.status, int):
            self.status = (QueueEnum.eq.value, self.status)
