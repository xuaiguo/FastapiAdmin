"""MySQL 多数据源示例 Schema"""

from pydantic import BaseModel, ConfigDict, Field


class MysqlDemoCreateSchema(BaseModel):
    """创建"""

    name: str = Field(..., min_length=1, max_length=100, description="名称")
    description: str | None = Field(default=None, max_length=500, description="描述")
    status: int = Field(default=0, ge=0, le=1, description="状态(0:启用 1:禁用)")


class MysqlDemoUpdateSchema(MysqlDemoCreateSchema):
    """更新"""


class MysqlDemoOutSchema(MysqlDemoCreateSchema):
    """响应"""

    id: int

    model_config = ConfigDict(from_attributes=True)
