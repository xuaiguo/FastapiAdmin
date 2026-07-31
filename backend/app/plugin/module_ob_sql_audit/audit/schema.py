"""OB 实时 SQL 审计 Schema"""

from pydantic import BaseModel, ConfigDict


class ObSqlAuditOutSchema(BaseModel):
    """SQL 审计查询结果"""

    request_type: int | None = None
    consistency_level: int | None = None
    request_time: str | None = None
    request_memory_mb: float | None = None
    ret_code: int | None = None
    query_sql: str | None = None
    sql_id: str | None = None
    stmt_type: str | None = None
    tenant_name: str | None = None
    effective_tenant_id: int | None = None
    user_name: str | None = None
    db_name: str | None = None
    plan_id: int | None = None
    elapsed_time_ms: float | None = None
    execute_time_ms: float | None = None
    total_wait_time_ms: float | None = None
    get_plan_time_ms: float | None = None
    disk_reads: int | None = None
    affected_rows: int | None = None
    return_rows: int | None = None
    partition_cnt: int | None = None
    wait_time_micro_ms: float | None = None
    event: str | None = None
    total_waits: int | None = None
    trace_id: str | None = None
    rpc_count: int | None = None
    plan_type: int | None = None
    is_inner_sql: int | None = None
    is_executor_rpc: int | None = None
    is_hit_plan: int | None = None
    net_time_ms: float | None = None
    net_wait_time_ms: float | None = None
    queue_time_ms: float | None = None
    decode_time_ms: float | None = None
    application_wait_time_ms: float | None = None
    concurrency_wait_time_ms: float | None = None
    user_io_wait_time_ms: float | None = None
    schedule_time_ms: float | None = None
    row_cache_hit: int | None = None
    bloom_filter_cache_hit: int | None = None
    block_cache_hit: int | None = None
    retry_cnt: int | None = None
    table_scan: int | None = None
    memstore_read_row_count: int | None = None
    ssstore_read_row_count: int | None = None
    expected_worker_count: int | None = None
    used_worker_count: int | None = None
    tx_id: str | int | None = None
    svr_ip: str | None = None
    client_ip: str | None = None

    model_config = ConfigDict(from_attributes=True)
