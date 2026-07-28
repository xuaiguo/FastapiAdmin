"""OB 分区表分析 Schema"""

from pydantic import BaseModel, ConfigDict


class ObPartitionTabAnalyzeOutSchema(BaseModel):
    """分区表分析查询结果"""

    table_owner: str | None = None
    composite: str | None = None
    partitioning_type: str | None = None
    subpartitioning_type: str | None = None
    o_partition_updater: str | None = None
    table_name: str | None = None
    is_max_partition: int | None = None
    first_partition: str | None = None
    final_partition: str | None = None
    plan_auto_interval: str | None = None
    column_list: str | None = None
    sub_column_list: str | None = None
    auto_interval: str | None = None
    global_count: int | None = None
    local_count: int | None = None
    compression: str | None = None
    partition_count: int | None = None
    subpartition_count: int | None = None

    model_config = ConfigDict(from_attributes=True)
