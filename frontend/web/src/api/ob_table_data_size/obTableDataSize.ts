import { request } from "@utils";

const API_PATH = "/ob_table_data_size";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObTableDataSizeAPI = {
  /** 获取 OB Oracle 数据源列表（按模块+用户过滤） */
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },

  /** 查询租户表大小统计 */
  listTableDataSize(query?: ObTableDataSizePageQuery) {
    return request<ApiResponse<PageResult<ObTableDataSizeRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObTableDataSizeAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  host?: string;
  service_name?: string;
}

export interface ObTableDataSizePageQuery extends PageQuery {
  config_id?: number;
  svr_ip?: string;
  database_name?: string;
  object_name?: string;
  order_by?: string;
  order_dir?: string;
}

export interface ObTableDataSizeRow {
  svr_ip?: string;
  svr_port?: number;
  database_name?: string;
  object_type?: string;
  object_name?: string;
  data_size_mb?: number;
  required_size_mb?: number;
}
