"""OB Oracle SQL 查询 Schema"""

from pydantic import BaseModel, Field


class ObOracleQueryRequest(BaseModel):
    """SQL 查询请求"""

    config_id: int = Field(..., description="数据源配置 ID")
    sql: str = Field(..., min_length=1, max_length=50000, description="SQL 语句")
    max_rows: int = Field(default=1000, ge=1, le=10000, description="最大返回行数")
    module_name: str | None = Field(default=None, description="当前模块名称，用于数据源权限校验")


class ObOracleQueryResponse(BaseModel):
    """SQL 查询响应"""

    columns: list[str] = Field(default_factory=list, description="列名列表")
    rows: list[list] = Field(default_factory=list, description="数据行")
    total: int = Field(default=0, description="返回行数")
    truncated: bool = Field(default=False, description="结果是否被截断")
    elapsed_ms: float = Field(default=0, description="执行耗时(ms)")


class QueryHistoryCreateSchema(BaseModel):
    """查询历史创建"""

    config_id: int = Field(..., description="数据源配置ID")
    config_name: str | None = Field(default=None, description="数据源名称")
    sql: str = Field(..., description="SQL语句")
    status: int = Field(default=0, description="执行状态(0:成功 1:失败)")
    elapsed_ms: float | None = Field(default=None, description="执行耗时(ms)")
    row_count: int | None = Field(default=None, description="返回行数")
    error_msg: str | None = Field(default=None, description="错误信息")


class QueryHistoryUpdateSchema(BaseModel):
    """查询历史更新"""

    config_id: int | None = None
    config_name: str | None = None
    sql: str | None = None
    status: int | None = None
    elapsed_ms: float | None = None
    row_count: int | None = None
    error_msg: str | None = None
