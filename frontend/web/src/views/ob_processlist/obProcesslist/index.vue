<!-- OB ProcessList 查询 -->
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
import ObProcesslistAPI, {
  type ObOracleConfigOption,
  type ObProcesslistPageQuery,
  type ObProcesslistRow,
} from "@/api/ob_processlist/obProcesslist";

defineOptions({ name: "ObProcesslist", inheritAttrs: false });

// ====== 数据源选择 ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObProcesslistAPI.listObOracleConfigs({ module_name: moduleName.value });
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
type ProcesslistSearchForm = {
  user?: string;
  db?: string;
  state?: string;
  info?: string;
  user_client_ip?: string;
  sql_id?: string;
  trace_id?: string;
};

const searchForm = ref<ProcesslistSearchForm>({
  user: undefined, db: undefined, state: undefined,
  info: undefined, user_client_ip: undefined, sql_id: undefined, trace_id: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const stateOptions = [
  { label: "Sleep", value: "Sleep" },
  { label: "Active", value: "Active" },
];

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "用户", key: "user", type: "input", span: 3, props: { placeholder: "用户（模糊）", clearable: true } },
  { label: "数据库", key: "db", type: "input", span: 3, props: { placeholder: "数据库（模糊）", clearable: true } },
  { label: "状态", key: "state", type: "select", span: 3, props: { placeholder: "状态", clearable: true, options: stateOptions } },
  { label: "SQL文本", key: "info", type: "input", span: 4, props: { placeholder: "SQL文本（模糊）", clearable: true } },
  { label: "客户端IP", key: "user_client_ip", type: "input", span: 3, props: { placeholder: "客户端IP（模糊）", clearable: true } },
  { label: "SQL ID", key: "sql_id", type: "input", span: 4, props: { placeholder: "SQL ID（模糊）", clearable: true } },
  { label: "Trace ID", key: "trace_id", type: "input", span: 4, props: { placeholder: "Trace ID（模糊）", clearable: true } },
]);

// ====== 排序 ======
const sortState = ref<{ order_by?: string; order_dir?: string }>({
  order_by: "TIME",
  order_dir: "desc",
});

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortState.value = {
    order_by: prop ? prop.toUpperCase() : "TIME",
    order_dir: order === "ascending" ? "asc" : "desc",
  };
  handleSearchBarSearch(searchForm.value);
}

// ====== 查询构建 ======
function buildQueryParams(form: ProcesslistSearchForm): ObProcesslistPageQuery {
  const params: ObProcesslistPageQuery = {
    page_no: 1,
    page_size: pagination.size || 20,
    config_id: selectedConfigId.value,
    order_by: sortState.value.order_by,
    order_dir: sortState.value.order_dir,
  };
  if (form.user) params.user = form.user;
  if (form.db) params.db = form.db;
  if (form.state) params.state = form.state;
  if (form.info) params.info = form.info;
  if (form.user_client_ip) params.user_client_ip = form.user_client_ip;
  if (form.sql_id) params.sql_id = form.sql_id;
  if (form.trace_id) params.trace_id = form.trace_id;
  return params;
}

async function handleSearchBarSearch(form: ProcesslistSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = {
    user: undefined, db: undefined, state: undefined,
    info: undefined, user_client_ip: undefined, sql_id: undefined, trace_id: undefined,
  };
  sortState.value = { order_by: "TIME", order_dir: "desc" };
  replaceSearchParams(buildQueryParams(searchForm.value));
  getData();
}

// ====== 表格 ======
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

const fmt = (row: ObProcesslistRow, key: keyof ObProcesslistRow) =>
  (row[key] as number | undefined)?.toLocaleString();

const {
  columns, columnChecks, data, loading, pagination,
  getData, replaceSearchParams,
  handleSizeChange, handleCurrentChange,
  refreshData,
} = useTable({
  core: {
    apiFn: ObProcesslistAPI.listProcesslist,
    apiParams: { page_no: 1, page_size: 20, config_id: 1, order_by: "TIME", order_dir: "desc" } as ObProcesslistPageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "id", label: "ID", width: 80, align: "right" },
      { prop: "svr_ip", label: "服务IP", width: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "user", label: "用户", width: 100, sortable: "custom" },
      { prop: "host", label: "主机", width: 160, sortable: "custom", showOverflowTooltip: true },
      { prop: "db", label: "数据库", width: 100 },
      { prop: "tenant", label: "租户", width: 100 },
      { prop: "command", label: "命令", width: 100, sortable: "custom" },
      { prop: "time", label: "时间(s)", width: 100, align: "right", sortable: "custom", formatter: (row: ObProcesslistRow) => fmt(row, "time") },
      { prop: "total_time", label: "总时间(us)", width: 110, align: "right", sortable: "custom", formatter: (row: ObProcesslistRow) => fmt(row, "total_time") },
      { prop: "state", label: "状态", width: 120, sortable: "custom" },
      { prop: "info", label: "SQL文本", minWidth: 200, showOverflowTooltip: true },
      { prop: "user_client_ip", label: "客户端IP", width: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "user_host", label: "客户端主机", width: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "sql_id", label: "SQL ID", width: 160, sortable: "custom", showOverflowTooltip: true },
      { prop: "trans_id", label: "事务ID", width: 120, showOverflowTooltip: true },
      { prop: "trace_id", label: "Trace ID", width: 180, sortable: "custom", showOverflowTooltip: true },
      { prop: "top_trace_id", label: "Top Trace ID", width: 180, showOverflowTooltip: true },
      { prop: "module", label: "模块", width: 120, sortable: "custom", showOverflowTooltip: true },
      { prop: "action", label: "动作", width: 100, showOverflowTooltip: true },
      { prop: "client_info", label: "客户端信息", width: 140, showOverflowTooltip: true },
    ],
  },
});
</script>
