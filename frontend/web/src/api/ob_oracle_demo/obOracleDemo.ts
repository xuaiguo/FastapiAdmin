import { request } from "@utils";

const API_PATH = "/ob_oracle_demo/ob_oracle_demo";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObOracleDemoAPI = {
  /** 获取可用的 OceanBase Oracle 数据源列表 */
  listObOracleConfigs() {
    return request<ApiResponse<PageResult<ObOracleConfigOption>>>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0 },
    });
  },

  listObOracleDemo(query?: ObOracleDemoPageQuery) {
    return request<ApiResponse<PageResult<ObOracleDemoTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailObOracleDemo(id: number, configId: number) {
    return request<ApiResponse<ObOracleDemoTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
      params: { config_id: configId },
    });
  },

  createObOracleDemo(body: ObOracleDemoForm, configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      params: { config_id: configId },
      data: body,
    });
  },

  updateObOracleDemo(id: number, body: ObOracleDemoForm, configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      params: { config_id: configId },
      data: body,
    });
  },

  deleteObOracleDemo(body: number[], configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      params: { config_id: configId },
      data: body,
    });
  },
};

export default ObOracleDemoAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  host: string;
  port: number;
  service_name: string;
}

export interface ObOracleDemoPageQuery extends PageQuery {
  name?: string;
  status?: number;
  config_id?: number;
}

export interface ObOracleDemoTable {
  id?: number;
  name?: string;
  description?: string;
  status?: number;
}

export interface ObOracleDemoForm {
  id?: number;
  name?: string;
  description?: string;
  status?: number;
}
