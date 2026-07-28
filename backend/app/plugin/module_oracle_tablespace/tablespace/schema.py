"""Oracle 表空间查询 Schema"""

from pydantic import BaseModel, ConfigDict, Field


class OracleTablespaceOutSchema(BaseModel):
    """表空间查询结果"""

    tablespace_type: str = Field(description="类型: USER / TEMP")
    tablespace_name: str = Field(description="表空间名称")
    autoext: str = Field(description="自动扩展: YES / NO")
    max_mb: float = Field(description="最大容量 MB")
    os_file_mb: float = Field(description="文件分配 MB")
    used_mb: float = Field(description="已用 MB")
    pct_used: float = Field(description="使用率 %")

    model_config = ConfigDict(from_attributes=True)
