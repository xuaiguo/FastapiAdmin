import { request } from "@utils";

const API_PATH = "/system/ob_oracle_config";

const ObOracleConfigAPI = {
  listObOracleConfig(query?: ObOracleConfigPageQuery) {
    return request<ApiResponse<PageResult<ObOracleConfigTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailObOracleConfig(id: number) {
    return request<ApiResponse<ObOracleConfigTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createObOracleConfig(body: ObOracleConfigForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateObOracleConfig(id: number, body: ObOracleConfigForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteObOracleConfig(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchObOracleConfig(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  testConnection(id: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/test/${id}`,
      method: "post",
    });
  },
};

export default ObOracleConfigAPI;

export interface ObOracleConfigPageQuery extends PageQuery {
  name?: string;
  host?: string;
  status?: number;
}

export interface ObOracleConfigTable extends BaseType {
  name?: string;
  host?: string;
  port?: number;
  service_name?: string;
  username?: string;
  password?: string;
  pool_size?: number;
  max_overflow?: number;
  status?: number;
  remark?: string;
}

export interface ObOracleConfigForm extends BaseFormType {
  name?: string;
  host?: string;
  port?: number;
  service_name?: string;
  username?: string;
  password?: string;
  pool_size?: number;
  max_overflow?: number;
  status?: number;
  remark?: string;
}
