import { request } from "@utils";

const API_PATH = "/system/mysql_config";

const MysqlConfigAPI = {
  listMysqlConfig(query?: MysqlConfigPageQuery) {
    return request<ApiResponse<PageResult<MysqlConfigTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailMysqlConfig(id: number) {
    return request<ApiResponse<MysqlConfigTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createMysqlConfig(body: MysqlConfigForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateMysqlConfig(id: number, body: MysqlConfigForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteMysqlConfig(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchMysqlConfig(body: BatchType) {
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

export default MysqlConfigAPI;

export interface MysqlConfigPageQuery extends PageQuery {
  name?: string;
  host?: string;
  status?: number;
}

export interface MysqlConfigTable extends BaseType {
  name?: string;
  host?: string;
  port?: number;
  database_name?: string;
  username?: string;
  password?: string;
  pool_size?: number;
  max_overflow?: number;
  db_model?: string;
  charset?: string;
  status?: number;
  remark?: string;
}

export interface MysqlConfigForm extends BaseFormType {
  name?: string;
  host?: string;
  port?: number;
  database_name?: string;
  username?: string;
  password?: string;
  pool_size?: number;
  max_overflow?: number;
  db_model?: string;
  charset?: string;
  status?: number;
  remark?: string;
}
