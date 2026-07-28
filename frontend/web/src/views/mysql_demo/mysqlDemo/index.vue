<!-- MySQL Demo 数据管理（连接 MySQL 租户数据库） -->
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
      >
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_mysql_demo:demo:create']"
            :perm-delete="['module_mysql_demo:demo:delete']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @delete="handleBatchDelete"
          />
        </template>
      </FaTableHeader>

      <FaTable
        ref="faTableRef"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @selection-change="onTableSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="600px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="dialogVisible.type === 'detail' ? handleCloseDialog() : handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions :column="2" :data="detailFormData" :items="detailItems" max-height="75vh" />
      </template>
      <template v-else>
        <FaForm
          scrollbar
          max-height="75vh"
          :key="formRenderKey"
          ref="dataFormRef"
          v-model="formData"
          :items="formItems"
          :rules="rules"
          label-suffix=":"
          :label-width="100"
          label-position="right"
          :span="24"
          :show-reset="false"
          :show-submit="false"
          class="crud-dialog-art-form"
        >
          <template #status>
            <ElRadioGroup v-model="formData.status">
              <ElRadio :value="0">启用</ElRadio>
              <ElRadio :value="1">禁用</ElRadio>
            </ElRadioGroup>
          </template>
        </FaForm>
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { useTable } from "@/hooks/core/useTable";
import { useCrudDialog } from "@/hooks/core/useCrudDialog";
import { useCrudForm } from "@/hooks/core/useCrudForm";
import { confirmDelete, confirmBatchDelete } from "@/hooks/core/useConfirm";
import { useTableSelection } from "@/hooks/core/useTableSelection";
import { useAuth } from "@/hooks/core/useAuth";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type FaForm from "@/components/forms/fa-form/index.vue";
import { resolveStatusColumns, renderTableOperationCell } from "@utils";
import MysqlDemoAPI, {
  type MysqlConfigOption,
  type MysqlDemoForm,
  type MysqlDemoPageQuery,
  type MysqlDemoTable,
} from "@/api/mysql_demo/mysqlDemo";

defineOptions({ name: "MysqlDemo", inheritAttrs: false });

const { hasAuth } = useAuth();

// ====== 数据源选择 ======
const configList = ref<MysqlConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await MysqlDemoAPI.listMysqlConfigs();
    const resData = (res as any)?.data;
    const payload = resData?.data || resData || {};
    const rows = payload.items || payload.rows || [];
    configList.value = rows as MysqlConfigOption[];
    if (configList.value.length > 0) {
      selectedConfigId.value = configList.value[0]!.id;
      replaceSearchParams(buildQueryParams(searchForm.value));
    }
  } catch { /* ignore */ }
});

// 切换数据源 → 当作搜索条件变更处理
function onConfigChange() {
  handleSearchBarSearch(searchForm.value);
}

// ====== 搜索 ======
type MysqlSearchForm = { name?: string; status?: number; config_id?: number };

const searchForm = ref<MysqlSearchForm>({ name: undefined, status: undefined });
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const statusOptions = ref([
  { label: "启用", value: 0 },
  { label: "禁用", value: 1 },
]);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "名称", key: "name", type: "input", props: { placeholder: "请输入名称", clearable: true }, span: 6 },
  { label: "状态", key: "status", type: "select", props: { placeholder: "请选择状态", options: statusOptions.value, clearable: true }, span: 6 },
]);

function buildQueryParams(form: MysqlSearchForm): MysqlSearchForm {
  return { ...form, config_id: selectedConfigId.value };
}

async function handleSearchBarSearch(form: MysqlSearchForm) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildQueryParams(form));
  getData();
}

function onResetSearch() {
  searchForm.value = { name: undefined, status: undefined };
  replaceSearchParams(buildQueryParams(searchForm.value));
  getData();
}

// ====== 表格选择 ======
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedIds, batchDeleting, onTableSelectionChange } = useTableSelection<MysqlDemoTable>();

// ====== 行操作 ======
type RowAction = { key: string; label: string; artType: "add" | "edit" | "delete" | "view" | "more"; perm: string; run: () => void };

function buildRowActions(row: MysqlDemoTable, ctx: { onDetail: (id: number) => void; onEdit: (id: number) => void; onDelete: (id: number) => void }): RowAction[] {
  const all: RowAction[] = [
    { key: "detail", label: "详情", artType: "view", perm: "module_mysql_demo:demo:detail", run: () => ctx.onDetail(row.id!) },
    { key: "edit", label: "编辑", artType: "edit", perm: "module_mysql_demo:demo:update", run: () => ctx.onEdit(row.id!) },
    { key: "delete", label: "删除", artType: "delete", perm: "module_mysql_demo:demo:delete", run: () => ctx.onDelete(row.id!) },
  ];
  return all.filter((a) => hasAuth(a.perm));
}

function formatOperationCell(row: MysqlDemoTable, ctx: Parameters<typeof buildRowActions>[1]) {
  return renderTableOperationCell(buildRowActions(row, ctx), { wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1" });
}

const createLoading = ref(false);

const opCtx = {
  onDetail: (id: number) => void handleOpenDialog("detail", id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deleteRow,
};

// ====== useTable（标准模式） ======
const {
  columns, columnChecks, data, loading, pagination,
  getData, replaceSearchParams,
  handleSizeChange, handleCurrentChange,
  refreshData, refreshCreate, refreshUpdate, refreshRemove,
} = useTable({
  core: {
    apiFn: MysqlDemoAPI.listMysqlDemo,
    apiParams: { page_no: 1, page_size: 10, config_id: 1 } as MysqlDemoPageQuery,
    immediate: false,
    columnsFactory: resolveStatusColumns<MysqlDemoTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "id", label: "ID", width: 80 },
      { prop: "name", label: "名称", minWidth: 150, showOverflowTooltip: true },
      { prop: "description", label: "描述", minWidth: 200, showOverflowTooltip: true },
      { prop: "operation", label: "操作", width: 200, fixed: "right", align: "center", formatter: (row: MysqlDemoTable) => formatOperationCell(row, opCtx) },
    ]),
  },
});

// ====== CRUD 弹窗 ======
const initialFormData: MysqlDemoForm = { id: undefined, name: undefined, description: undefined, status: 0 };
const formData = ref<MysqlDemoForm>({ ...initialFormData });
const { dialogVisible } = useCrudDialog();
const detailFormData = ref<Record<string, unknown>>({});
const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const formRenderKey = ref(0);

const rules = reactive({
  name: [{ required: true, message: "请输入名称", trigger: "blur" }],
});

const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } = useCrudForm<MysqlDemoForm>({
  formData,
  initialFormData,
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: (id: number) => MysqlDemoAPI.detailMysqlDemo(id, selectedConfigId.value),
  createApi: (body: MysqlDemoForm) => MysqlDemoAPI.createMysqlDemo(body, selectedConfigId.value),
  updateApi: (id: number, body: MysqlDemoForm) => MysqlDemoAPI.updateMysqlDemo(id, body, selectedConfigId.value),
  titles: { create: "新增数据", update: "修改数据", detail: "数据详情" },
  detailFormData,
  onCreateSuccess: async () => { await refreshCreate(); },
  onUpdateSuccess: async () => { await refreshUpdate(); },
});

const formItems = computed<FormItem[]>(() => [
  { label: "名称", key: "name", type: "input", span: 24, props: { placeholder: "请输入名称", maxlength: 100 } },
  { label: "描述", key: "description", type: "input", span: 24, props: { placeholder: "请输入描述", maxlength: 500 } },
  { label: "状态", key: "status", type: "custom", span: 24 },
]);

const detailItems: import("@/components/others/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "ID", prop: "id" },
  { label: "名称", prop: "name" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "禁用" } } } },
  { label: "描述", prop: "description", span: 4 },
];

async function handleAdd() {
  createLoading.value = true;
  try { await handleOpenDialog("create"); } finally { createLoading.value = false; }
}

// ====== 删除 ======
async function deleteRow(id: number) {
  await confirmDelete();
  await MysqlDemoAPI.deleteMysqlDemo([id], selectedConfigId.value);
  faTableRef.value?.elTableRef?.clearSelection();
  await refreshRemove();
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return;
  await confirmBatchDelete(selectedIds.value.length);
  batchDeleting.value = true;
  try {
    await MysqlDemoAPI.deleteMysqlDemo(selectedIds.value, selectedConfigId.value);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } finally { batchDeleting.value = false; }
}
</script>
