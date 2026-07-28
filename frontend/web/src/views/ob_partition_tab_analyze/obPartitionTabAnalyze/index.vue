<!-- OB 分区表分析 -->
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
import { useRoute } from "vue-router";
import { useTable } from "@/hooks/core/useTable";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import ObPartitionTabAnalyzeAPI, {
  type ObOracleConfigOption,
  type ObPartitionTabAnalyzePageQuery,
  type ObPartitionTabAnalyzeRow,
} from "@/api/ob_partition_tab_analyze/obPartitionTabAnalyze";

defineOptions({ name: "ObPartitionTabAnalyze", inheritAttrs: false });

// ====== 数据源选择 ======
const route = useRoute();
const moduleName = computed(() => route.name as string);
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObPartitionTabAnalyzeAPI.listObOracleConfigs({ module_name: moduleName.value });
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
type AnalyzeSearchForm = {
  table_owner?: string;
  table_name?: string;
};

const searchForm = ref<AnalyzeSearchForm>({
  table_owner: undefined,
  table_name: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "表所有者", key: "table_owner", type: "input", span: 6, props: { placeholder: "如 MON", clearable: true } },
  { label: "表名", key: "table_name", type: "input", span: 6, props: { placeholder: "表名（模糊搜索）", clearable: true } },
]);

// ====== 查询构建 ======
function buildQueryParams(form: AnalyzeSearchForm): ObPartitionTabAnalyzePageQuery {
  const params: ObPartitionTabAnalyzePageQuery = {
    page_no: 1,
    page_size: pagination.size || 20,
    config_id: selectedConfigId.value,
  };
  if (form.table_owner) {
    params.table_owner = form.table_owner;
  }
  if (form.table_name) {
    params.table_name = form.table_name;
  }
  return params;
}

async function handleSearchBarSearch(form: AnalyzeSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = { table_owner: undefined, table_name: undefined };
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
    apiFn: ObPartitionTabAnalyzeAPI.listAnalyze,
    apiParams: { page_no: 1, page_size: 20, config_id: 1 } as ObPartitionTabAnalyzePageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "table_owner", label: "表所有者", width: 120 },
      { prop: "table_name", label: "表名", minWidth: 180, showOverflowTooltip: true },
      { prop: "composite", label: "复合分区", width: 100 },
      { prop: "partitioning_type", label: "分区类型", width: 110 },
      { prop: "subpartitioning_type", label: "子分区类型", width: 110 },
      { prop: "o_partition_updater", label: "维护方式", width: 130 },
      { prop: "is_max_partition", label: "MAX分区", width: 100, align: "center" },
      { prop: "first_partition", label: "首分区", width: 140, showOverflowTooltip: true },
      { prop: "final_partition", label: "末分区", width: 140, showOverflowTooltip: true },
      { prop: "plan_auto_interval", label: "自动Interval", width: 120 },
      { prop: "column_list", label: "分区键列", minWidth: 200, showOverflowTooltip: true },
      { prop: "sub_column_list", label: "子分区键列", minWidth: 160, showOverflowTooltip: true },
      { prop: "auto_interval", label: "间隔", width: 120, showOverflowTooltip: true },
      { prop: "global_count", label: "全局索引", width: 100, align: "right" },
      { prop: "local_count", label: "本地索引", width: 100, align: "right" },
      { prop: "compression", label: "压缩", width: 90 },
      { prop: "partition_count", label: "分区数", width: 90, align: "right" },
      { prop: "subpartition_count", label: "子分区数", width: 100, align: "right" },
    ],
  },
});
</script>
