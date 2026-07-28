<!-- OB 实时 SQL 审计 -->
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
      :is-expand="true"
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
import ObSqlAuditAPI, {
  type ObOracleConfigOption,
  type ObSqlAuditPageQuery,
  type ObSqlAuditRow,
} from "@/api/ob_sql_audit/obSqlAudit";

defineOptions({ name: "ObSqlAudit", inheritAttrs: false });

// ====== 数据源选择 ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObSqlAuditAPI.listObOracleConfigs({ module_name: moduleName.value });
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
  const begin = new Date(now.getTime() - 10 * 60 * 1000); // 当前时间 - 10分钟
  const end = new Date(now.getTime() + 60 * 60 * 1000);   // 当前时间 + 1小时
  return [formatDateTime(begin), formatDateTime(end)];
}

// ====== 搜索 ======
type AuditSearchForm = {
  time_range?: string[];
  trace_id?: string;
  sql_id?: string;
  ret_code_min?: number;
  ret_code_max?: number;
  memory_min?: number;
  memory_max?: number;
};

const searchForm = ref<AuditSearchForm>({
  time_range: getDefaultTimeRange(),
  trace_id: undefined,
  sql_id: undefined,
  ret_code_min: undefined,
  ret_code_max: undefined,
  memory_min: undefined,
  memory_max: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "时间范围", key: "time_range", type: "datetimerange", span: 6, props: { placeholder: ["开始时间", "结束时间"] } },
  { label: "Trace ID", key: "trace_id", type: "input", span: 3, labelWidth: "90px",props: { placeholder: "Trace ID", clearable: true } },
  { label: "SQL ID", key: "sql_id", type: "input", span: 3, props: { placeholder: "SQL ID", clearable: true } },
  { label: "返回码Min", key: "ret_code_min", type: "input", span: 3, labelWidth: "90px", props: { placeholder: "-10000", clearable: true } },
  { label: "Max", key: "ret_code_max", type: "input", span: 2, labelWidth: "60px", props: { placeholder: "0", clearable: true } },
  { label: "内存Min", key: "memory_min", type: "input", span: 2, labelWidth: "70px", props: { placeholder: "0", clearable: true } },
  { label: "Max", key: "memory_max", type: "input", span: 2, labelWidth: "60px", props: { placeholder: "1024", clearable: true } },
]);

// ====== 排序 ======
const sortState = ref<{ order_by?: string; order_dir?: string }>({
  order_by: "REQUEST_TIME",
  order_dir: "desc",
});

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortState.value = {
    order_by: prop ? prop.toUpperCase() : "REQUEST_TIME",
    order_dir: order === "ascending" ? "asc" : "desc",
  };
  handleSearchBarSearch(searchForm.value);
}

// ====== 查询构建 ======
function buildQueryParams(form: AuditSearchForm): ObSqlAuditPageQuery {
  const params: ObSqlAuditPageQuery = {
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
  if (form.trace_id) params.trace_id = form.trace_id;
  if (form.sql_id) params.sql_id = form.sql_id;
  if (form.ret_code_min !== undefined && form.ret_code_min !== null) params.ret_code_min = Number(form.ret_code_min);
  if (form.ret_code_max !== undefined && form.ret_code_max !== null) params.ret_code_max = Number(form.ret_code_max);
  if (form.memory_min !== undefined && form.memory_min !== null) params.memory_min = Number(form.memory_min);
  if (form.memory_max !== undefined && form.memory_max !== null) params.memory_max = Number(form.memory_max);
  return params;
}

async function handleSearchBarSearch(form: AuditSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = {
    time_range: getDefaultTimeRange(), trace_id: undefined, sql_id: undefined,
    ret_code_min: undefined, ret_code_max: undefined,
    memory_min: undefined, memory_max: undefined,
  };
  sortState.value = { order_by: "REQUEST_TIME", order_dir: "desc" };
  replaceSearchParams(buildQueryParams(searchForm.value));
  getData();
}

// ====== 表格 ======
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

const fmt = (row: ObSqlAuditRow, key: keyof ObSqlAuditRow) =>
  (row[key] as number | undefined)?.toLocaleString();

const {
  columns, columnChecks, data, loading, pagination,
  getData, replaceSearchParams,
  handleSizeChange, handleCurrentChange,
  refreshData,
} = useTable({
  core: {
    apiFn: ObSqlAuditAPI.listSqlAudit,
    apiParams: { page_no: 1, page_size: 20, config_id: 1, order_by: "REQUEST_TIME", order_dir: "desc" } as ObSqlAuditPageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "request_time", label: "请求时间", width: 170, sortable: "custom" },
      { prop: "sql_id", label: "SQL ID", minWidth: 160, showOverflowTooltip: true },
      { prop: "query_sql", label: "SQL 文本", minWidth: 200, showOverflowTooltip: true },
      { prop: "ret_code", label: "返回码", width: 90, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "ret_code") },
      { prop: "user_name", label: "用户", width: 100 },
      { prop: "db_name", label: "数据库", width: 100 },
      { prop: "tenant_name", label: "租户", width: 100 },
      { prop: "elapsed_time_ms", label: "总耗时(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "elapsed_time_ms") },
      { prop: "execute_time_ms", label: "执行时间(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "execute_time_ms") },
      { prop: "total_wait_time_ms", label: "等待总时间(ms)", width: 140, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "total_wait_time_ms") },
      { prop: "request_memory_mb", label: "内存(MB)", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "request_memory_mb") },
      { prop: "disk_reads", label: "物理读", width: 90, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "disk_reads") },
      { prop: "affected_rows", label: "影响行数", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "affected_rows") },
      { prop: "return_rows", label: "返回行数", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "return_rows") },
      { prop: "rpc_count", label: "RPC数", width: 80, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "rpc_count") },
      { prop: "trace_id", label: "Trace ID", minWidth: 180, showOverflowTooltip: true },
      { prop: "stmt_type", label: "语句类型", width: 100 },
      { prop: "plan_id", label: "Plan ID", width: 100, align: "right" },
      { prop: "plan_type", label: "计划类型", width: 90, align: "right" },
      { prop: "is_hit_plan", label: "命中缓存", width: 90, align: "center" },
      { prop: "get_plan_time_ms", label: "获计划时间(ms)", width: 130, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "get_plan_time_ms") },
      { prop: "wait_time_micro_ms", label: "等待事件(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "wait_time_micro_ms") },
      { prop: "event", label: "等待事件", width: 120, showOverflowTooltip: true },
      { prop: "net_time_ms", label: "网络时间(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "net_time_ms") },
      { prop: "queue_time_ms", label: "队列时间(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "queue_time_ms") },
      { prop: "decode_time_ms", label: "Decode(ms)", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "decode_time_ms") },
      { prop: "application_wait_time_ms", label: "Application(ms)", width: 130, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "application_wait_time_ms") },
      { prop: "concurrency_wait_time_ms", label: "Concurrency(ms)", width: 130, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "concurrency_wait_time_ms") },
      { prop: "user_io_wait_time_ms", label: "UserIO(ms)", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "user_io_wait_time_ms") },
      { prop: "schedule_time_ms", label: "Schedule(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "schedule_time_ms") },
      { prop: "block_cache_hit", label: "块缓存命中", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "block_cache_hit") },
      { prop: "row_cache_hit", label: "行缓存命中", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "row_cache_hit") },
      { prop: "retry_cnt", label: "重试次数", width: 90, align: "right", sortable: "custom", formatter: (row: ObSqlAuditRow) => fmt(row, "retry_cnt") },
      { prop: "table_scan", label: "全表扫描", width: 90, align: "center" },
      { prop: "svr_ip", label: "服务IP", width: 140, showOverflowTooltip: true },
      { prop: "client_ip", label: "客户端IP", width: 140, showOverflowTooltip: true },
    ],
  },
});
</script>
