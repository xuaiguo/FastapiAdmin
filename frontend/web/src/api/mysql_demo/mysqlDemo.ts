import { request } from "@utils";

const API_PATH = "/mysql_demo/mysql_demo";
const CONFIG_PATH = "/system/mysql_config";

const MysqlDemoAPI = {
  /** 获取可用的 MySQL 数据源列表 */
  listMysqlConfigs() {
    return request<ApiResponse<PageResult<MysqlConfigOption>>>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, db_model: "local" },
    });
  },

  listMysqlDemo(query?: MysqlDemoPageQuery) {
    return request<ApiResponse<PageResult<MysqlDemoTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailMysqlDemo(id: number, configId: number) {
    return request<ApiResponse<MysqlDemoTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
      params: { config_id: configId },
    });
  },

  createMysqlDemo(body: MysqlDemoForm, configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      params: { config_id: configId },
      data: body,
    });
  },

  updateMysqlDemo(id: number, body: MysqlDemoForm, configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      params: { config_id: configId },
      data: body,
    });
  },

  deleteMysqlDemo(body: number[], configId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      params: { config_id: configId },
      data: body,
    });
  },
};

export default MysqlDemoAPI;

export interface MysqlConfigOption {
  id: number;
  name: string;
  host: string;
  port: number;
  database_name: string;
}

export interface MysqlDemoPageQuery extends PageQuery {
  name?: string;
  status?: number;
  config_id?: number;
}

export interface MysqlDemoTable {
  id?: number;
  name?: string;
  description?: string;
  status?: number;
}

export interface MysqlDemoForm {
  id?: number;
  name?: string;
  description?: string;
  status?: number;
}
