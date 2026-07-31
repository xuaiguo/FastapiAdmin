<!-- Oracle 会话查询（连接 Oracle v$session） -->
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
      />
    </ElCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useTable } from "@/hooks/core/useTable";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import OracleSessionAPI, {
  type OracleConfigOption,
  type OracleSessionPageQuery,
} from "@/api/oracle_session/oracleSession";

defineOptions({ name: "OracleSession", inheritAttrs: false });

// ====== 数据源选择 ======
const configList = ref<OracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await OracleSessionAPI.listOracleConfigs();
    const resData = (res as any)?.data;
    const payload = resData?.data || resData || {};
    const rows = payload.items || payload.rows || [];
    configList.value = rows as OracleConfigOption[];
    if (configList.value.length > 0) {
      selectedConfigId.value = configList.value[0]!.id;
      replaceSearchParams(buildQueryParams(searchForm.value));
      // 不自动查询，等用户主动选择数据源或点击搜索后再查
    }
  } catch { /* ignore */ }
});

function onConfigChange() {
  handleSearchBarSearch(searchForm.value);
}

// ====== 搜索 ======
type SessionSearchForm = {
  service_name?: string;
  schemaname?: string;
  module?: string;
  program?: string;
  status?: string;
  logon_time?: string[];
  config_id?: number;
};

const searchForm = ref<SessionSearchForm>({
  service_name: undefined,
  schemaname: undefined,
  module: undefined,
  program: undefined,
  status: undefined,
  logon_time: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const statusOptions = ref([
  { label: "ACTIVE", value: "ACTIVE" },
  { label: "INACTIVE", value: "INACTIVE" },
]);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "服务名", key: "service_name", type: "input", props: { placeholder: "服务名", clearable: true }, span: 4 },
  { label: "Schema", key: "schemaname", type: "input", props: { placeholder: "Schema名", clearable: true }, span: 4 },
  { label: "模块", key: "module", type: "input", props: { placeholder: "模块名", clearable: true }, span: 4 },
  { label: "程序", key: "program", type: "input", props: { placeholder: "程序名", clearable: true }, span: 4 },
  { label: "状态", key: "status", type: "select", props: { placeholder: "状态", options: statusOptions.value, clearable: true }, span: 4 },
  { label: "登录时间", key: "logon_time", type: "datetimerange", span: 8 },
]);

function buildQueryParams(form: SessionSearchForm): OracleSessionPageQuery {
  const params: OracleSessionPageQuery = {
    page_no: 1,
    page_size: pagination.size || 10,
    config_id: selectedConfigId.value,
    service_name: form.service_name || undefined,
    schemaname: form.schemaname || undefined,
    module: form.module || undefined,
    program: form.program || undefined,
    status: form.status || undefined,
  };
  if (form.logon_time && form.logon_time.length === 2) {
    params.logon_time_start = form.logon_time[0];
    params.logon_time_end = form.logon_time[1];
  }
  return params;
}

async function handleSearchBarSearch(form: SessionSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = {
    service_name: undefined,
    schemaname: undefined,
    module: undefined,
    program: undefined,
    status: undefined,
    logon_time: undefined,
  };
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
    apiFn: OracleSessionAPI.listOracleSession,
    apiParams: { page_no: 1, page_size: 10, config_id: 1 } as OracleSessionPageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "sid", label: "SID", width: 70 },
      { prop: "serial_no", label: "Serial#", width: 80 },
      { prop: "service_name", label: "服务名", minWidth: 100, showOverflowTooltip: true },
      { prop: "schemaname", label: "Schema", minWidth: 90, showOverflowTooltip: true },
      { prop: "module", label: "模块", minWidth: 110, showOverflowTooltip: true },
      { prop: "program", label: "程序", minWidth: 110, showOverflowTooltip: true },
      {
        prop: "status", label: "状态", width: 100,
        status: {
          ACTIVE: { type: "success", text: "ACTIVE" },
          INACTIVE: { type: "warning", text: "INACTIVE" },
        },
      },
      { prop: "machine", label: "机器名", minWidth: 120, showOverflowTooltip: true },
      { prop: "terminal", label: "终端", minWidth: 90, showOverflowTooltip: true },
      { prop: "osuser", label: "OS用户", minWidth: 90, showOverflowTooltip: true },
      { prop: "sql_id", label: "SQL ID", minWidth: 100, showOverflowTooltip: true },
      { prop: "logon_time", label: "登录时间", width: 170, showOverflowTooltip: true },
      { prop: "prev_exec_start", label: "上次执行时间", width: 170, showOverflowTooltip: true },
    ],
  },
});
</script>
