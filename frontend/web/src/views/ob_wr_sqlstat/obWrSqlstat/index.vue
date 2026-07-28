<!-- OB SQL 性能统计 -->
<template>
  <div class="fa-full-height">
    <!-- 数据源选择器 -->
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
import ObWrSqlstatAPI, {
  type ObOracleConfigOption,
  type ObWrSqlstatPageQuery,
  type ObWrSqlstatRow,
} from "@/api/ob_wr_sqlstat/obWrSqlstat";

defineOptions({ name: "ObWrSqlstat", inheritAttrs: false });

// ====== 数据源选择 ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObWrSqlstatAPI.listObOracleConfigs({ module_name: moduleName.value });
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

// ====== 默认时间范围 ======
function formatDateTime(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function getDefaultTimeRange(): string[] {
  const now = new Date();
  const begin = new Date(now.getTime() - 30 * 60 * 1000); // 当前时间 - 10分钟
  const end = new Date(now.getTime() + 60 * 60 * 1000);   // 当前时间 + 1小时
  return [formatDateTime(begin), formatDateTime(end)];
}

// ====== 搜索 ======
type SqlstatSearchForm = {
  time_range?: string[];
  parsing_db_name?: string;
  sql_id?: string;
};

const searchForm = ref<SqlstatSearchForm>({
  time_range: getDefaultTimeRange(),
  parsing_db_name: undefined,
  sql_id: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "时间范围", key: "time_range", type: "datetimerange", span: 8, props: { placeholder: ["开始时间", "结束时间"] } },
  { label: "数据库名", key: "parsing_db_name", type: "input", span: 4, props: { placeholder: "数据库名", clearable: true } },
  { label: "SQL ID", key: "sql_id", type: "input", span: 4, props: { placeholder: "SQL ID", clearable: true } },
]);

// ====== 排序 ======
const sortState = ref<{ order_by?: string; order_dir?: string }>({
  order_by: "END_INTERVAL_TIME",
  order_dir: "desc",
});

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortState.value = {
    order_by: prop ? prop.toUpperCase() : "END_INTERVAL_TIME",
    order_dir: order === "ascending" ? "asc" : "desc",
  };
  handleSearchBarSearch(searchForm.value);
}

// ====== 查询构建 ======
function buildQueryParams(form: SqlstatSearchForm): ObWrSqlstatPageQuery {
  const params: ObWrSqlstatPageQuery = {
    page_no: 1,
    page_size: pagination.size || 20,
    config_id: selectedConfigId.value,
    order_by: sortState.value.order_by,
    order_dir: sortState.value.order_dir,
  };
  if (form.time_range && form.time_range.length === 2) {
    params.begin_time = form.time_range[0];
    params.end_time = form.time_range[1];
  }
  if (form.parsing_db_name) {
    params.parsing_db_name = form.parsing_db_name;
  }
  if (form.sql_id) {
    params.sql_id = form.sql_id;
  }
  return params;
}

async function handleSearchBarSearch(form: SqlstatSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = { time_range: getDefaultTimeRange(), parsing_db_name: undefined, sql_id: undefined };
  sortState.value = { order_by: "END_INTERVAL_TIME", order_dir: "desc" };
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
    apiFn: ObWrSqlstatAPI.listSqlstat,
    apiParams: { page_no: 1, page_size: 20, config_id: 1, order_by: "END_INTERVAL_TIME", order_dir: "desc" } as ObWrSqlstatPageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "begin_interval_time", label: "开始时间", width: 160, sortable: "custom" },
      { prop: "end_interval_time", label: "结束时间", width: 160, sortable: "custom" },
      { prop: "sql_id", label: "SQL ID", minWidth: 180, showOverflowTooltip: true },
      { prop: "query_sql", label: "SQL 文本", minWidth: 200, showOverflowTooltip: true },
      { prop: "parsing_db_name", label: "数据库名", width: 120 },
      { prop: "elapsed_time_delta_ms", label: "耗时(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.elapsed_time_delta_ms?.toLocaleString() },
      { prop: "elapsed_time_delta_ms_per_exec", label: "每次耗时(ms)", width: 130, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.elapsed_time_delta_ms_per_exec?.toLocaleString() },
      { prop: "executions_delta", label: "执行次数", width: 100, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.executions_delta?.toLocaleString() },
      { prop: "cpu_time_delta_ms", label: "CPU(ms)", width: 100, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.cpu_time_delta_ms?.toLocaleString() },
      { prop: "disk_reads_delta", label: "磁盘读", width: 100, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.disk_reads_delta?.toLocaleString() },
      { prop: "buffer_gets_delta", label: "缓冲读", width: 100, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.buffer_gets_delta?.toLocaleString() },
      { prop: "ccwait_delta_ms", label: "CC等待(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.ccwait_delta_ms?.toLocaleString() },
      { prop: "userio_wait_delta_ms", label: "IO等待(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.userio_wait_delta_ms?.toLocaleString() },
      { prop: "apwait_delta_ms", label: "应用等待(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.apwait_delta_ms?.toLocaleString() },
      { prop: "rows_processed_delta", label: "处理行数", width: 110, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.rows_processed_delta?.toLocaleString() },
      { prop: "fetches_delta", label: "获取次数", width: 100, align: "right", sortable: "custom", formatter: (row: ObWrSqlstatRow) => row.fetches_delta?.toLocaleString() },
      { prop: "source_ip", label: "来源IP", width: 140, showOverflowTooltip: true },
      { prop: "module", label: "模块", width: 120, showOverflowTooltip: true },
      { prop: "snap_id", label: "快照ID", width: 90, align: "right" },
    ],
  },
});
</script>
