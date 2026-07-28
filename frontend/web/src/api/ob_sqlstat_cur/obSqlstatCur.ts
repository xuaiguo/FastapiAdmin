import { request } from "@utils";

const API_PATH = "/ob_sqlstat_cur";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObSqlstatCurAPI = {
  /** 获取 OB Oracle 数据源列表（按模块+用户过滤） */
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },

  /** 查询实时 SQL 性能统计 */
  listSqlstatCur(query?: ObSqlstatCurPageQuery) {
    return request<ApiResponse<PageResult<ObSqlstatCurRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObSqlstatCurAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  host?: string;
  service_name?: string;
}

export interface ObSqlstatCurPageQuery extends PageQuery {
  config_id?: number;
  parsing_db_name?: string;
  sql_id?: string;
  order_by?: string;
  order_dir?: string;
}

export interface ObSqlstatCurRow {
  parsing_db_name?: string;
  sql_id?: string;
  query_sql?: string;
  plan_id?: number;
  elapsed_time_delta_ms?: number;
  elapsed_time_delta_ms_per_exec?: number;
  executions_delta?: number;
  cpu_time_delta_ms?: number;
  disk_reads_delta?: number;
  buffer_gets_delta?: number;
  ccwait_delta_ms?: number;
  userio_wait_delta_ms?: number;
  apwait_delta_ms?: number;
  physical_read_requests_delta?: number;
  physical_read_bytes_delta?: number;
  write_throttle_delta?: number;
  rows_processed_delta?: number;
  memstore_read_rows_delta?: number;
  minor_ssstore_read_rows_delta?: number;
  major_ssstore_read_rows_delta?: number;
  rpc_delta?: number;
  fetches_delta?: number;
  retry_delta?: number;
  partition_delta?: number;
  nested_sql_delta?: number;
  route_miss_delta?: number;
  source_ip?: string;
  tenant_id?: number;
  plan_hash?: number;
  plan_type?: number;
  module?: string;
  action?: string;
}
