import { request } from "@utils";

const API_PATH = "/ob_partition_tab_analyze";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObPartitionTabAnalyzeAPI = {
  /** 获取 OB Oracle 数据源列表（按模块+用户过滤） */
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },

  /** 查询分区表分析 */
  listAnalyze(query?: ObPartitionTabAnalyzePageQuery) {
    return request<ApiResponse<PageResult<ObPartitionTabAnalyzeRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObPartitionTabAnalyzeAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  host?: string;
  service_name?: string;
}

export interface ObPartitionTabAnalyzePageQuery extends PageQuery {
  config_id?: number;
  table_owner?: string;
  table_name?: string;
}

export interface ObPartitionTabAnalyzeRow {
  table_owner?: string;
  composite?: string;
  partitioning_type?: string;
  subpartitioning_type?: string;
  o_partition_updater?: string;
  table_name?: string;
  is_max_partition?: number;
  first_partition?: string;
  final_partition?: string;
  plan_auto_interval?: string;
  column_list?: string;
  sub_column_list?: string;
  auto_interval?: string;
  global_count?: number;
  local_count?: number;
  compression?: string;
  partition_count?: number;
  subpartition_count?: number;
}
