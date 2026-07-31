import { request } from "@utils";

const API_PATH = "/oracle_demo/oracle_demo";
const CONFIG_PATH = "/system/oracle_config";

const OracleDemoAPI = {
  /** 获取可用的 Oracle 数据源列表 */
  listOracleConfigs() {
    return request<ApiResponse<PageResult<OracleConfigOption>>>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, db_type: "PDB", auth_mode: "NORMAL" },
    });
  },

  listOracleDemo(query?: OracleDemoPageQuery) {
    return request<ApiResponse<PageResult<OracleDemoTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailOracleDemo(id: number, configId: number) {
    return request<ApiResponse<OracleDemoTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
      params: { config_id: configId },
    });
  },

  createOracleDemo(body: OracleDemoForm, configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      params: { config_id: configId },
      data: body,
    });
  },

  updateOracleDemo(id: number, body: OracleDemoForm, configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      params: { config_id: configId },
      data: body,
    });
  },

  deleteOracleDemo(body: number[], configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      params: { config_id: configId },
      data: body,
    });
  },
};

export default OracleDemoAPI;

export interface OracleConfigOption {
  id: number;
  name: string;
  host: string;
  port: number;
  service_name: string;
}

export interface OracleDemoPageQuery extends PageQuery {
  name?: string;
  status?: number;
  config_id?: number;
}

export interface OracleDemoTable {
  id?: number;
  name?: string;
  description?: string;
  status?: number;
}

export interface OracleDemoForm {
  id?: number;
  name?: string;
  description?: string;
  status?: number;
}
