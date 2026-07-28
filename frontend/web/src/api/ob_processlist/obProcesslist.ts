import { request } from "@utils";

const API_PATH = "/ob_processlist";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObProcesslistAPI = {
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },
  listProcesslist(query?: ObProcesslistPageQuery) {
    return request<ApiResponse<PageResult<ObProcesslistRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObProcesslistAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  service_name?: string;
}

export interface ObProcesslistPageQuery extends PageQuery {
  config_id?: number;
  user?: string;
  db?: string;
  state?: string;
  info?: string;
  user_client_ip?: string;
  sql_id?: string;
  trace_id?: string;
  order_by?: string;
  order_dir?: string;
}

export interface ObProcesslistRow {
  id?: number;
  svr_ip?: string;
  user?: string;
  host?: string;
  db?: string;
  tenant?: string;
  command?: string;
  time?: number;
  total_time?: number;
  state?: string;
  info?: string;
  user_client_ip?: string;
  user_host?: string;
  sql_id?: string;
  trans_id?: string;
  trace_id?: string;
  top_trace_id?: string;
  module?: string;
  action?: string;
  client_info?: string;
}
