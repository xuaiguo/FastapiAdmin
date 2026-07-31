<!-- OB 实时 SQL 性能统计 -->
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
import ObSqlstatCurAPI, {
  type ObOracleConfigOption,
  type ObSqlstatCurPageQuery,
  type ObSqlstatCurRow,
} from "@/api/ob_sqlstat_cur/obSqlstatCur";

defineOptions({ name: "ObSqlstatCur", inheritAttrs: false });

// ====== 数据源选择 ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObSqlstatCurAPI.listObOracleConfigs({ module_name: moduleName.value });
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
type SqlstatCurSearchForm = {
  parsing_db_name?: string;
  sql_id?: string;
};

const searchForm = ref<SqlstatCurSearchForm>({
  parsing_db_name: undefined,
  sql_id: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "数据库名", key: "parsing_db_name", type: "input", span: 6, props: { placeholder: "数据库名", clearable: true } },
  { label: "SQL ID", key: "sql_id", type: "input", span: 6, props: { placeholder: "SQL ID（模糊搜索）", clearable: true } },
]);

// ====== 排序 ======
const sortState = ref<{ order_by?: string; order_dir?: string }>({
  order_by: "ELAPSED_TIME_DELTA_MS_PER_EXEC",
  order_dir: "desc",
});

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortState.value = {
    order_by: prop ? prop.toUpperCase() : "ELAPSED_TIME_DELTA_MS_PER_EXEC",
    order_dir: order === "ascending" ? "asc" : "desc",
  };
  handleSearchBarSearch(searchForm.value);
}

// ====== 查询构建 ======
function buildQueryParams(form: SqlstatCurSearchForm): ObSqlstatCurPageQuery {
  const params: ObSqlstatCurPageQuery = {
    page_no: 1,
    page_size: pagination.size || 20,
    config_id: selectedConfigId.value,
    order_by: sortState.value.order_by,
    order_dir: sortState.value.order_dir,
  };
  if (form.parsing_db_name) {
    params.parsing_db_name = form.parsing_db_name;
  }
  if (form.sql_id) {
    params.sql_id = form.sql_id;
  }
  return params;
}

async function handleSearchBarSearch(form: SqlstatCurSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = { parsing_db_name: undefined, sql_id: undefined };
  sortState.value = { order_by: "ELAPSED_TIME_DELTA_MS_PER_EXEC", order_dir: "desc" };
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
    apiFn: ObSqlstatCurAPI.listSqlstatCur,
    apiParams: { page_no: 1, page_size: 20, config_id: 1, order_by: "ELAPSED_TIME_DELTA_MS_PER_EXEC", order_dir: "desc" } as ObSqlstatCurPageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "sql_id", label: "SQL ID", minWidth: 180, showOverflowTooltip: true },
      { prop: "query_sql", label: "SQL 文本", minWidth: 200, showOverflowTooltip: true },
      { prop: "parsing_db_name", label: "数据库名", width: 120 },
      { prop: "plan_id", label: "Plan ID", width: 100, align: "right" },
      { prop: "elapsed_time_delta_ms", label: "耗时(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.elapsed_time_delta_ms?.toLocaleString() },
      { prop: "elapsed_time_delta_ms_per_exec", label: "每次耗时(ms)", width: 130, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.elapsed_time_delta_ms_per_exec?.toLocaleString() },
      { prop: "executions_delta", label: "执行次数", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.executions_delta?.toLocaleString() },
      { prop: "cpu_time_delta_ms", label: "CPU(ms)", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.cpu_time_delta_ms?.toLocaleString() },
      { prop: "disk_reads_delta", label: "磁盘读", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.disk_reads_delta?.toLocaleString() },
      { prop: "buffer_gets_delta", label: "缓冲读", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.buffer_gets_delta?.toLocaleString() },
      { prop: "ccwait_delta_ms", label: "CC等待(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.ccwait_delta_ms?.toLocaleString() },
      { prop: "userio_wait_delta_ms", label: "IO等待(ms)", width: 110, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.userio_wait_delta_ms?.toLocaleString() },
      { prop: "apwait_delta_ms", label: "应用等待(ms)", width: 120, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.apwait_delta_ms?.toLocaleString() },
      { prop: "rows_processed_delta", label: "处理行数", width: 110, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.rows_processed_delta?.toLocaleString() },
      { prop: "fetches_delta", label: "获取次数", width: 100, align: "right", sortable: "custom", formatter: (row: ObSqlstatCurRow) => row.fetches_delta?.toLocaleString() },
      { prop: "source_ip", label: "来源IP", width: 140, showOverflowTooltip: true },
      { prop: "tenant_id", label: "租户ID", width: 90, align: "right" },
      { prop: "module", label: "模块", width: 120, showOverflowTooltip: true },
      { prop: "action", label: "动作", width: 100, showOverflowTooltip: true },
    ],
  },
});
</script>
