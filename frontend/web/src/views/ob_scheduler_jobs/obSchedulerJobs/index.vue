<!-- OB JOBS 查询 -->
<template>
  <div class="fa-full-height">
    <div class="flex items-center gap-3 px-4 py-2">
      <span class="text-sm font-medium">数据源：</span>
      <ElSelect v-model="selectedConfigId" style="width: 280px" @change="onConfigChange">
        <ElOption v-for="c in configList" :key="c.id" :label="c.name" :value="c.id" />
      </ElSelect>
    </div>

    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="searchItems"
      :is-expand="false"
      :show-reset="true"
      :show-search="true"
      @search="handleSearchBarSearch"
      @reset="onResetSearch"
    />

    <ElCard class="fa-table-card" :style="{ 'margin-top': showSearchBar ? '12px' : '0' }">
      <FaTableHeader
        v-model:columns="columnChecks"
        v-model:showSearchBar="showSearchBar"
        :loading="loading"
        @refresh="refreshData"
      />
      <FaTable
        ref="faTableRef"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
        @sort-change="onSortChange"
      />
    </ElCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useTable } from "@/hooks/core/useTable";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import ObSchedulerJobsAPI, {
  type ObOracleConfigOption,
  type ObSchedulerJobsPageQuery,
  type ObSchedulerJobsRow,
} from "@/api/ob_scheduler_jobs/obSchedulerJobs";

defineOptions({ name: "ObSchedulerJobs", inheritAttrs: false });

// ====== 数据源选择 ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObSchedulerJobsAPI.listObOracleConfigs({ module_name: moduleName.value });
    const resData = (res as any)?.data;
    const payload = resData?.data || resData || {};
    const rows = payload.items || payload.rows || [];
    configList.value = rows as ObOracleConfigOption[];
    if (configList.value.length > 0) {
      selectedConfigId.value = configList.value[0]!.id;
    }
  } catch {
    // 静默处理
  }
});

function onConfigChange() {
  handleSearchBarSearch(searchForm.value);
}

// ====== 搜索 ======
type JobsSearchForm = {
  owner?: string;
  job_name?: string;
  job_action?: string;
};

const searchForm = ref<JobsSearchForm>({
  owner: undefined,
  job_name: undefined,
  job_action: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "所有者", key: "owner", type: "input", span: 6, props: { placeholder: "如 MON", clearable: true } },
  { label: "任务名称", key: "job_name", type: "input", span: 6, props: { placeholder: "任务名称（模糊搜索）", clearable: true } },
  { label: "任务动作", key: "job_action", type: "input", span: 12, props: { placeholder: "任务动作（模糊搜索）", clearable: true } },
]);

// ====== 排序 ======
const sortState = ref<{ order_by?: string; order_dir?: string }>({
  order_by: "JOB_NAME",
  order_dir: "asc",
});

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortState.value = {
    order_by: prop ? prop.toUpperCase() : "JOB_NAME",
    order_dir: order === "ascending" ? "asc" : "desc",
  };
  handleSearchBarSearch(searchForm.value);
}

// ====== 查询构建 ======
function buildQueryParams(form: JobsSearchForm): ObSchedulerJobsPageQuery {
  const params: ObSchedulerJobsPageQuery = {
    page_no: 1,
    page_size: pagination.size || 20,
    config_id: selectedConfigId.value,
    order_by: sortState.value.order_by,
    order_dir: sortState.value.order_dir,
  };
  if (form.owner) params.owner = form.owner;
  if (form.job_name) params.job_name = form.job_name;
  if (form.job_action) params.job_action = form.job_action;
  return params;
}

async function handleSearchBarSearch(form: JobsSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = { owner: undefined, job_name: undefined, job_action: undefined };
  sortState.value = { order_by: "JOB_NAME", order_dir: "asc" };
  replaceSearchParams(buildQueryParams(searchForm.value));
  getData();
}

// ====== 表格 ======
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

const {
  columns, columnChecks, data, loading, pagination,
  getData, replaceSearchParams,
  handleSizeChange, handleCurrentChange,
  refreshData,
} = useTable({
  core: {
    apiFn: ObSchedulerJobsAPI.listJobs,
    apiParams: { page_no: 1, page_size: 20, config_id: 1, order_by: "JOB_NAME", order_dir: "asc" } as ObSchedulerJobsPageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "owner", label: "所有者", width: 100 },
      { prop: "job_name", label: "任务名称", minWidth: 180, sortable: "custom", showOverflowTooltip: true },
      { prop: "job_style", label: "风格", width: 90 },
      { prop: "job_type", label: "类型", width: 110 },
      { prop: "job_class", label: "类别", width: 110 },
      { prop: "job_action", label: "任务动作", minWidth: 200, sortable: "custom", showOverflowTooltip: true },
      { prop: "repeat_interval", label: "重复间隔", width: 140, showOverflowTooltip: true },
      { prop: "last_start_date", label: "上次执行时间", width: 170, sortable: "custom" },
      { prop: "next_run_date", label: "下次执行时间", width: 170, sortable: "custom" },
      { prop: "program_name", label: "程序名", width: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "schedule_name", label: "调度名", width: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "enabled", label: "启用", width: 80, sortable: "custom", align: "center" },
      { prop: "state", label: "状态", width: 100, sortable: "custom" },
      { prop: "comments", label: "备注", minWidth: 160, showOverflowTooltip: true },
      { prop: "max_run_duration", label: "最大运行时长", width: 130 },
    ],
  },
});
</script>
