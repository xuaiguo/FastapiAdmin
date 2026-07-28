import { request } from "@utils";

const API_PATH = "/system/oracle_config";

const OracleConfigAPI = {
  listOracleConfig(query?: OracleConfigPageQuery) {
    return request<ApiResponse<PageResult<OracleConfigTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailOracleConfig(id: number) {
    return request<ApiResponse<OracleConfigTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createOracleConfig(body: OracleConfigForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateOracleConfig(id: number, body: OracleConfigForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteOracleConfig(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchOracleConfig(body: BatchType) {
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

export default OracleConfigAPI;

export interface OracleConfigPageQuery extends PageQuery {
  name?: string;
  host?: string;
  db_type?: string;
  auth_mode?: string;
  status?: number;
}

export interface OracleConfigTable extends BaseType {
  name?: string;
  host?: string;
  port?: number;
  service_name?: string;
  db_type?: string;
  auth_mode?: string;
  username?: string;
  password?: string;
  pool_size?: number;
  max_overflow?: number;
  status?: number;
  remark?: string;
}

export interface OracleConfigForm extends BaseFormType {
  name?: string;
  host?: string;
  port?: number;
  service_name?: string;
  db_type?: string;
  auth_mode?: string;
  username?: string;
  password?: string;
  pool_size?: number;
  max_overflow?: number;
  status?: number;
  remark?: string;
}
