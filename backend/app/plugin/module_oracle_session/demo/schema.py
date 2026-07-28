"""Oracle 会话查询 Schema"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OracleSessionQueryParam(BaseModel):
    """查询参数"""
    service_name: str | None = Field(default=None, description="服务名（模糊）")
    schemaname: str | None = Field(default=None, description="Schema名（模糊）")
    module: str | None = Field(default=None, description="模块名（模糊）")
    program: str | None = Field(default=None, description="程序名（模糊）")
    status: str | None = Field(default=None, description="状态（等值: ACTIVE/INACTIVE）")
    logon_time_start: str | None = Field(default=None, description="登录时间起(yyyy-mm-dd hh24:mi:ss)")
    logon_time_end: str | None = Field(default=None, description="登录时间止(yyyy-mm-dd hh24:mi:ss)")


class OracleSessionOutSchema(BaseModel):
    """响应"""
    sid: int | None = None
    serial_no: int | None = None
    service_name: str | None = None
    schemaname: str | None = None
    module: str | None = None
    program: str | None = None
    status: str | None = None
    machine: str | None = None
    terminal: str | None = None
    osuser: str | None = None
    sql_id: str | None = None
    logon_time: datetime | None = None
    prev_exec_start: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
