"""OB SQL 性能统计 Schema"""

from pydantic import BaseModel, ConfigDict


class ObWrSqlstatOutSchema(BaseModel):
    """SQL 性能统计查询结果"""

    begin_interval_time: str | None = None
    end_interval_time: str | None = None
    sql_id: str | None = None
    query_sql: str | None = None
    parsing_db_name: str | None = None
    elapsed_time_delta_ms: float | None = None
    elapsed_time_delta_ms_per_exec: float | None = None
    executions_delta: int | None = None
    cpu_time_delta_ms: float | None = None
    disk_reads_delta: int | None = None
    buffer_gets_delta: int | None = None
    ccwait_delta_ms: float | None = None
    userio_wait_delta_ms: float | None = None
    apwait_delta_ms: float | None = None
    physical_read_requests_delta: int | None = None
    physical_read_bytes_delta: int | None = None
    write_throttle_delta: int | None = None
    rows_processed_delta: int | None = None
    memstore_read_rows_delta: int | None = None
    minor_ssstore_read_rows_delta: int | None = None
    major_ssstore_read_rows_delta: int | None = None
    rpc_delta: int | None = None
    fetches_delta: int | None = None
    retry_delta: int | None = None
    partition_delta: int | None = None
    nested_sql_delta: int | None = None
    route_miss_delta: int | None = None
    sql_type: int | None = None
    plan_hash: int | None = None
    plan_type: int | None = None
    snap_id: int | None = None
    source_ip: str | None = None
    module: str | None = None
    action: str | None = None

    model_config = ConfigDict(from_attributes=True)
