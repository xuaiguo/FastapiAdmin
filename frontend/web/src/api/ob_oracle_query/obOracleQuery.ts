import { request } from "@utils";

const API_PATH = "/ob_oracle_query";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObOracleQueryAPI = {
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },
  executeSql(data: { config_id: number; sql: string; max_rows?: number; module_name?: string }) {
    return request<ApiResponse<ObOracleQueryResult>>({
      url: `${API_PATH}/execute`,
      method: "post",
      data,
    });
  },
  listHistory(params: { page_no: number; page_size: number; config_id?: number; status?: number }) {
    return request<ApiResponse<PageResult<QueryHistoryRow>>>({
      url: `${API_PATH}/history/list`,
      method: "get",
      params,
    });
  },
  deleteHistory(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/history/delete`,
      method: "delete",
      data: ids,
    });
  },
  clearHistory() {
    return request<ApiResponse>({
      url: `${API_PATH}/history/clear`,
      method: "delete",
    });
  },
};

export default ObOracleQueryAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  service_name?: string;
}

export interface ObOracleQueryResult {
  columns: string[];
  rows: any[][];
  total: number;
  truncated: boolean;
  elapsed_ms: number;
}

export interface QueryHistoryRow {
  id: number;
  config_id: number;
  config_name?: string;
  sql: string;
  status: number;
  elapsed_ms?: number;
  row_count?: number;
  error_msg?: string;
  created_time: string;
  created_by?: { id: number; username: string; nickname?: string };
}
