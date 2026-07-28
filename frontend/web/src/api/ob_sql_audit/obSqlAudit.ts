import { request } from "@utils";

const API_PATH = "/ob_sql_audit";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObSqlAuditAPI = {
  /** 获取 OB Oracle 数据源列表（按模块+用户过滤） */
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },

  /** 查询 SQL 审计 */
  listSqlAudit(query?: ObSqlAuditPageQuery) {
    return request<ApiResponse<PageResult<ObSqlAuditRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObSqlAuditAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  host?: string;
  service_name?: string;
}

export interface ObSqlAuditPageQuery extends PageQuery {
  config_id?: number;
  begin_time?: string;
  end_time?: string;
  trace_id?: string;
  sql_id?: string;
  ret_code_min?: number;
  ret_code_max?: number;
  memory_min?: number;
  memory_max?: number;
  order_by?: string;
  order_dir?: string;
}

export interface ObSqlAuditRow {
  request_type?: number;
  consistency_level?: number;
  request_time?: string;
  request_memory_mb?: number;
  ret_code?: number;
  query_sql?: string;
  sql_id?: string;
  stmt_type?: string;
  tenant_name?: string;
  effective_tenant_id?: number;
  user_name?: string;
  db_name?: string;
  plan_id?: number;
  elapsed_time_ms?: number;
  execute_time_ms?: number;
  total_wait_time_ms?: number;
  get_plan_time_ms?: number;
  disk_reads?: number;
  affected_rows?: number;
  return_rows?: number;
  partition_cnt?: number;
  wait_time_micro_ms?: number;
  event?: string;
  total_waits?: number;
  trace_id?: string;
  rpc_count?: number;
  plan_type?: number;
  is_inner_sql?: number;
  is_executor_rpc?: number;
  is_hit_plan?: number;
  net_time_ms?: number;
  net_wait_time_ms?: number;
  queue_time_ms?: number;
  decode_time_ms?: number;
  application_wait_time_ms?: number;
  concurrency_wait_time_ms?: number;
  user_io_wait_time_ms?: number;
  schedule_time_ms?: number;
  row_cache_hit?: number;
  bloom_filter_cache_hit?: number;
  block_cache_hit?: number;
  retry_cnt?: number;
  table_scan?: number;
  memstore_read_row_count?: number;
  ssstore_read_row_count?: number;
  expected_worker_count?: number;
  used_worker_count?: number;
  tx_id?: string;
  svr_ip?: string;
  client_ip?: string;
}
