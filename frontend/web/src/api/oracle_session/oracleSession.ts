import { request } from "@utils";

const API_PATH = "/oracle_session/oracle_session";
const CONFIG_PATH = "/system/oracle_config";

const OracleSessionAPI = {
  listOracleConfigs() {
    return request<ApiResponse<PageResult<OracleConfigOption>>>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, db_type: "CDB", auth_mode: "SYSDBA" },
    });
  },

  listOracleSession(query?: OracleSessionPageQuery) {
    return request<ApiResponse<PageResult<OracleSessionTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailOracleSession(sid: number, configId: number) {
    return request<ApiResponse<OracleSessionTable>>({
      url: `${API_PATH}/detail/${sid}`,
      method: "get",
      params: { config_id: configId },
    });
  },
};

export default OracleSessionAPI;

export interface OracleConfigOption {
  id: number;
  name: string;
}

export interface OracleSessionPageQuery extends PageQuery {
  config_id?: number;
  service_name?: string;
  schemaname?: string;
  module?: string;
  program?: string;
  status?: string;
  logon_time_start?: string;
  logon_time_end?: string;
}

export interface OracleSessionTable {
  sid?: number;
  serial_no?: number;
  service_name?: string;
  schemaname?: string;
  module?: string;
  program?: string;
  status?: string;
  machine?: string;
  terminal?: string;
  osuser?: string;
  sql_id?: string;
  logon_time?: string;
  prev_exec_start?: string;
}
