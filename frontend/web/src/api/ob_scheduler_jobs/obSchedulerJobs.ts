import { request } from "@utils";

const API_PATH = "/ob_scheduler_jobs";
const CONFIG_PATH = "/system/ob_oracle_config";

const ObSchedulerJobsAPI = {
  listObOracleConfigs(params?: { module_name?: string }) {
    return request<ApiResponse>({
      url: `${CONFIG_PATH}/list`,
      method: "get",
      params: { page_no: 1, page_size: 100, status: 0, ...params },
    });
  },
  listJobs(query?: ObSchedulerJobsPageQuery) {
    return request<ApiResponse<PageResult<ObSchedulerJobsRow>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },
};

export default ObSchedulerJobsAPI;

export interface ObOracleConfigOption {
  id: number;
  name: string;
  service_name?: string;
}

export interface ObSchedulerJobsPageQuery extends PageQuery {
  config_id?: number;
  owner?: string;
  job_name?: string;
  job_action?: string;
  order_by?: string;
  order_dir?: string;
}

export interface ObSchedulerJobsRow {
  owner?: string;
  job_name?: string;
  job_style?: string;
  job_type?: string;
  job_class?: string;
  job_action?: string;
  repeat_interval?: string;
  last_start_date?: string;
  next_run_date?: string;
  program_name?: string;
  schedule_name?: string;
  enabled?: string;
  state?: string;
  comments?: string;
  max_run_duration?: string;
}
