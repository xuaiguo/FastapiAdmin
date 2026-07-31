import { request } from "@utils";

const API_PATH = "/ob_wr_sqlstat";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObWrSqlstatAPI = {
  /** 获取 OB Oracle 数据源列表（按模块+用户过滤） */
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },

  /** 查询 SQL 性能统计 */
  listSqlstat(query?: ObWrSqlstatPageQuery) {
    return request<ApiResponse<PageResult<ObWrSqlstatRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObWrSqlstatAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  host?: string;
  service_name?: string;
}

export interface ObWrSqlstatPageQuery extends PageQuery {
  config_id?: number;
  begin_time?: string;
  end_time?: string;
  parsing_db_name?: string;
  sql_id?: string;
  order_by?: string;
  order_dir?: string;
}

export interface ObWrSqlstatRow {
  begin_interval_time?: string;
  end_interval_time?: string;
  sql_id?: string;
  query_sql?: string;
  parsing_db_name?: string;
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
  sql_type?: number;
  plan_hash?: number;
  plan_type?: string;
  snap_id?: number;
  source_ip?: string;
  module?: string;
  action?: string;
}
