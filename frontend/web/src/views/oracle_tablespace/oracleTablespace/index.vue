<!-- Oracle 表空间查询 -->
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
        :default-sort="{ prop: 'pct_used', order: 'descending' }"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
        @sort-change="handleSortChange"
      />
    </ElCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useTable } from "@/hooks/core/useTable";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import OracleTablespaceAPI, {
  type OracleConfigOption,
  type OracleTablespacePageQuery,
  type OracleTablespaceRow,
} from "@/api/oracle_tablespace/oracleTablespace";

defineOptions({ name: "OracleTablespace", inheritAttrs: false });

// ====== 数据源选择 ======
const configList = ref<OracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await OracleTablespaceAPI.listOracleConfigs();
    const resData = (res as any)?.data;
    const payload = resData?.data || resData || {};
    const rows = payload.items || payload.rows || [];
    configList.value = rows as OracleConfigOption[];
    if (configList.value.length > 0) {
      selectedConfigId.value = configList.value[0]!.id;
      replaceSearchParams(buildQueryParams(searchForm.value));
      // 不自动查询，等用户主动选择数据源或点击搜索后再查
    } else {
      ElMessage.warning("暂无 PDB 数据源，请先在 Oracle 配置中添加 PDB 类型的数据源");
    }
  } catch {
    ElMessage.error("加载数据源列表失败，请检查网络或权限");
  }
});

function onConfigChange() {
  handleSearchBarSearch(searchForm.value);
}

// ====== 搜索 ======
type TablespaceSearchForm = {
  tablespace_type?: string;
  tablespace_name?: string;
  pct_used_min?: number;
  pct_used_max?: number;
  used_mb_min?: number;
  used_mb_max?: number;
};

const searchForm = ref<TablespaceSearchForm>({
  tablespace_type: undefined,
  tablespace_name: undefined,
  pct_used_min: undefined,
  pct_used_max: undefined,
  used_mb_min: undefined,
  used_mb_max: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const typeOptions = ref([
  { label: "USER", value: "USER" },
  { label: "TEMP", value: "TEMP" },
]);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "类型", key: "tablespace_type", type: "select", labelWidth: "40px", props: { placeholder: "全部", options: typeOptions.value, clearable: true }, span: 3 },
  { label: "表空间名", key: "tablespace_name", type: "input", labelWidth: "75px", props: { placeholder: "模糊匹配", clearable: true }, span: 3 },
  { label: "使用率最小(%)", key: "pct_used_min", type: "input-number", labelWidth: "120px", props: { placeholder: "最小", min: 0, max: 100, precision: 0 }, span: 3 },
  { label: "使用率最大(%)", key: "pct_used_max", type: "input-number", labelWidth: "120px", props: { placeholder: "最大", min: 0, max: 100, precision: 0 }, span: 3 },
  { label: "已用最小", key: "used_mb_min", type: "input-number", labelWidth: "70px", props: { placeholder: "最小MB", min: 0, precision: 0 }, span: 3 },
  { label: "已用最大", key: "used_mb_max", type: "input-number", labelWidth: "70px", props: { placeholder: "最大MB", min: 0, precision: 0 }, span: 3 },
]);

function buildQueryParams(form: TablespaceSearchForm): OracleTablespacePageQuery {
  const params: OracleTablespacePageQuery = {
    page_no: 1,
    page_size: pagination.size || 10,
    config_id: selectedConfigId.value,
    tablespace_type: form.tablespace_type || undefined,
    tablespace_name: form.tablespace_name || undefined,
    pct_used_min: form.pct_used_min ?? undefined,
    pct_used_max: form.pct_used_max ?? undefined,
    used_mb_min: form.used_mb_min ?? undefined,
    used_mb_max: form.used_mb_max ?? undefined,
    order_by: sortField.value,
    order_dir: sortOrder.value,
  };
  return params;
}

async function handleSearchBarSearch(form: TablespaceSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = {
    tablespace_type: undefined,
    tablespace_name: undefined,
    pct_used_min: undefined,
    pct_used_max: undefined,
    used_mb_min: undefined,
    used_mb_max: undefined,
  };
  replaceSearchParams(buildQueryParams(searchForm.value));
  getData();
}

// ====== 表格 ======
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);

// 排序状态
const sortField = ref<string>("pct_used");
const sortOrder = ref<string>("desc");

/** 处理列头点击排序（服务端排序） */
function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  if (order === null) {
    // 用户第三次点击取消排序，恢复默认
    sortField.value = "pct_used";
    sortOrder.value = "desc";
  } else {
    sortField.value = prop || "pct_used";
    sortOrder.value = order === "ascending" ? "asc" : "desc";
  }
  replaceSearchParams(buildQueryParams(searchForm.value));
  getData();
}

const {
  columns, columnChecks, data, loading, pagination,
  getData, replaceSearchParams,
  handleSizeChange, handleCurrentChange,
  refreshData,
} = useTable({
  core: {
    apiFn: OracleTablespaceAPI.listTablespace,
    apiParams: { page_no: 1, page_size: 10, config_id: 1 } as OracleTablespacePageQuery,
    immediate: false,
    columnsFactory: () => [
      { prop: "tablespace_type", label: "类型", width: 80, sortable: "custom", tag: { map: { USER: { type: "primary", text: "USER" }, TEMP: { type: "warning", text: "TEMP" } } } },
      { prop: "tablespace_name", label: "表空间名称", width: 300, sortable: "custom", showOverflowTooltip: true },
      { prop: "autoext", label: "自动扩展", width: 90, tag: { map: { YES: { type: "success", text: "YES" }, NO: { type: "info", text: "NO" } } } },
      { prop: "max_mb", label: "最大容量(MB)", width: 140, sortable: "custom", align: "right", formatter: (row: OracleTablespaceRow) => row.max_mb?.toLocaleString() },
      { prop: "os_file_mb", label: "文件分配(MB)", width: 140, sortable: "custom", align: "right", formatter: (row: OracleTablespaceRow) => row.os_file_mb?.toLocaleString() },
      { prop: "used_mb", label: "已用(MB)", width: 120, sortable: "custom", align: "right", formatter: (row: OracleTablespaceRow) => row.used_mb?.toLocaleString() },
      {
        prop: "pct_used", label: "使用率", width: 140, sortable: "custom", align: "center",
        formatter: (row: OracleTablespaceRow) => {
          const pct = row.pct_used ?? 0;
          const color = pct >= 90 ? "#F56C6C" : pct >= 70 ? "#E6A23C" : "#67C23A";
          return h("div", { style: { display: "flex", alignItems: "center", gap: "6px", justifyContent: "center" } }, [
            h("div", { style: { flex: "1", height: "8px", background: "#f0f0f0", borderRadius: "4px", overflow: "hidden", maxWidth: "60px" } }, [
              h("div", { style: { height: "100%", width: `${Math.min(pct, 100)}%`, background: color, borderRadius: "4px" } }),
            ]),
            h("span", { style: { fontSize: "12px", color, fontWeight: "500" } }, `${pct.toFixed(1)}%`),
          ]);
        },
      },
    ],
  },
});
</script>
