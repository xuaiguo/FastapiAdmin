"""OB 租户表大小统计 Schema"""

from pydantic import BaseModel, ConfigDict


class ObTableDataSizeOutSchema(BaseModel):
    """租户表大小统计查询结果"""

    svr_ip: str | None = None
    svr_port: int | None = None
    database_name: str | None = None
    object_type: str | None = None
    object_name: str | None = None
    data_size_mb: int | None = None
    required_size_mb: int | None = None

    model_config = ConfigDict(from_attributes=True)
