<!-- OB 租户表大小统计 -->
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
import ObTableDataSizeAPI, {
  type ObOracleConfigOption,
  type ObTableDataSizePageQuery,
  type ObTableDataSizeRow,
} from "@/api/ob_table_data_size/obTableDataSize";

defineOptions({ name: "ObTableDataSize", inheritAttrs: false });

// ====== 数据源选择（仅 Service Name = SYS 的 OB Oracle 数据源） ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObTableDataSizeAPI.listObOracleConfigs({ module_name: moduleName.value });
    const resData = (res as any)?.data;
    const payload = resData?.data || resData || {};
    const rows = payload.items || payload.rows || [];
    // 前端过滤：只保留 Service Name = SYS 的数据源
    configList.value = (rows as ObOracleConfigOption[]).filter(
      (c) => (c.service_name || "").toUpperCase() === "SYS"
    );
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
type TableDataSizeSearchForm = {
  svr_ip?: string;
  database_name?: string;
  object_name?: string;
};

const searchForm = ref<TableDataSizeSearchForm>({
  svr_ip: undefined,
  database_name: undefined,
  object_name: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "SVR IP", key: "svr_ip", type: "input", span: 4, props: { placeholder: "节点 IP", clearable: true } },
  { label: "数据库名", key: "database_name", type: "input", span: 4, props: { placeholder: "数据库名", clearable: true } },
  { label: "表名", key: "object_name", type: "input", span: 4, props: { placeholder: "表名", clearable: true } },
]);

// ====== 排序 ======
const sortState = ref<{ order_by?: string; order_dir?: string }>({
  order_by: "REQUIRED_SIZE_MB",
  order_dir: "desc",
});

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortState.value = {
    order_by: prop ? prop.toUpperCase() : "REQUIRED_SIZE_MB",
    order_dir: order === "ascending" ? "asc" : "desc",
  };
  handleSearchBarSearch(searchForm.value);
}

// ====== 查询构建 ======
function buildQueryParams(form: TableDataSizeSearchForm): ObTableDataSizePageQuery {
  const params: ObTableDataSizePageQuery = {
    page_no: 1,
    page_size: pagination.size || 20,
    config_id: selectedConfigId.value,
    order_by: sortState.value.order_by,
    order_dir: sortState.value.order_dir,
  };
  if (form.svr_ip) {
    params.svr_ip = form.svr_ip;
  }
  if (form.database_name) {
    params.database_name = form.database_name;
  }
  if (form.object_name) {
    params.object_name = form.object_name;
  }
  return params;
}

async function handleSearchBarSearch(form: TableDataSizeSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = { svr_ip: undefined, database_name: undefined, object_name: undefined };
  sortState.value = { order_by: "REQUIRED_SIZE_MB", order_dir: "desc" };
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
    apiFn: ObTableDataSizeAPI.listTableDataSize,
    apiParams: { page_no: 1, page_size: 20, config_id: 1, order_by: "REQUIRED_SIZE_MB", order_dir: "desc" } as ObTableDataSizePageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "svr_ip", label: "SVR IP", width: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "svr_port", label: "SVR 端口", width: 100, align: "right", formatter: (row: ObTableDataSizeRow) => row.svr_port?.toLocaleString() },
      { prop: "database_name", label: "数据库名", minWidth: 140, sortable: "custom", showOverflowTooltip: true },
      { prop: "object_type", label: "对象类型", width: 110, sortable: "custom" },
      { prop: "object_name", label: "表名", minWidth: 180, sortable: "custom", showOverflowTooltip: true },
      { prop: "data_size_mb", label: "数据大小(MB)", width: 130, align: "right", sortable: "custom", formatter: (row: ObTableDataSizeRow) => row.data_size_mb?.toLocaleString() },
      { prop: "required_size_mb", label: "占用空间(MB)", width: 130, align: "right", sortable: "custom", formatter: (row: ObTableDataSizeRow) => row.required_size_mb?.toLocaleString() },
    ],
  },
});
</script>
