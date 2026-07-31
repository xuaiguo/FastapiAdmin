import { request } from "@utils";

const API_PATH = "/oracle_tablespace";
const CONFIG_PATH = "/system/oracle_config";

const OracleTablespaceAPI = {
  /** 获取 PDB 数据源列表 */
  listOracleConfigs() {
    return request<ApiResponse<PageResult<OracleConfigOption>>>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, db_type: "PDB" },
    });
  },

  /** 查询表空间列表 */
  listTablespace(query?: OracleTablespacePageQuery) {
    return request<ApiResponse<PageResult<OracleTablespaceRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default OracleTablespaceAPI;

export interface OracleConfigOption {
  id: number;
  name: string;
  host?: string;
  db_type?: string;
}

export interface OracleTablespacePageQuery extends PageQuery {
  config_id?: number;
  tablespace_type?: string;
  tablespace_name?: string;
  pct_used_min?: number;
  pct_used_max?: number;
  used_mb_min?: number;
  used_mb_max?: number;
  order_by?: string;
  order_dir?: string;
}

export interface OracleTablespaceRow {
  tablespace_type: string;
  tablespace_name: string;
  autoext: string;
  max_mb: number;
  os_file_mb: number;
  used_mb: number;
  pct_used: number;
}
