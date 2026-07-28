<!-- MySQL 配置管理 -->
<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="searchItems"
      :is-expand="false"
      :show-reset="true"
      :show-search="true"
      @search="handleSearch"
      @reset="handleReset"
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
            :perm-create="['module_system:mysql_config:create']"
            :perm-delete="['module_system:mysql_config:delete']"
            :perm-patch="['module_system:mysql_config:patch']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @more="(handleMoreClick as any)"
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
      width="700px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
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
          :label-width="130"
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
          <template #password>
            <ElInput v-model="formData.password" type="password" show-password placeholder="请输入密码" />
          </template>
        </FaForm>
      </template>
    </FaDialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { ElMessage } from "element-plus";
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
import MysqlConfigAPI, {
  type MysqlConfigForm,
  type MysqlConfigPageQuery,
  type MysqlConfigTable,
} from "@/api/module_system/mysqlConfig";

defineOptions({ name: "MysqlConfig", inheritAttrs: false });

const { hasAuth } = useAuth();

// ====== 搜索 ======
type SearchForm = { name?: string; host?: string; db_model?: string; status?: number };
const searchForm = ref<SearchForm>({ name: undefined, host: undefined, db_model: undefined, status: undefined });
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);

const statusOptions = ref([
  { label: "启用", value: 0 },
  { label: "禁用", value: 1 },
]);

const dbModelOptions = ref([
  { label: "本地", value: "local" },
  { label: "云数据库", value: "cloud" },
  { label: "OceanBase", value: "oceanbase" },
]);

const searchItems = computed<SearchFormItem[]>(() => [
  { label: "实例名称", key: "name", type: "input", props: { placeholder: "请输入实例名称", clearable: true }, span: 6 },
  { label: "主机地址", key: "host", type: "input", props: { placeholder: "请输入主机地址", clearable: true }, span: 6 },
  { label: "数据库模型", key: "db_model", type: "select", labelWidth: "90px", props: { placeholder: "请选择模型", options: dbModelOptions.value, clearable: true }, span: 6 },
  { label: "状态", key: "status", type: "select", props: { placeholder: "请选择状态", options: statusOptions.value, clearable: true }, span: 6 },
]);

// ====== 表格选择 ======
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } = useTableSelection<MysqlConfigTable>();

// ====== 行操作 ======
type RowAction = { key: string; label: string; artType: "add" | "edit" | "delete" | "view" | "more"; perm: string; run: () => void };

function buildRowActions(row: MysqlConfigTable, ctx: { onDetail: (id: number) => void; onEdit: (id: number) => void; onDelete: (id: number) => void; onTest: (id: number) => void }): RowAction[] {
  const all: RowAction[] = [
    { key: "test", label: "测试连接", artType: "more", perm: "module_system:mysql_config:test", run: () => ctx.onTest(row.id!) },
    { key: "detail", label: "详情", artType: "view", perm: "module_system:mysql_config:detail", run: () => ctx.onDetail(row.id!) },
    { key: "edit", label: "编辑", artType: "edit", perm: "module_system:mysql_config:update", run: () => ctx.onEdit(row.id!) },
    { key: "delete", label: "删除", artType: "delete", perm: "module_system:mysql_config:delete", run: () => ctx.onDelete(row.id!) },
  ];
  return all.filter((a) => hasAuth(a.perm));
}

function formatOperationCell(row: MysqlConfigTable, ctx: Parameters<typeof buildRowActions>[1]) {
  return renderTableOperationCell(buildRowActions(row, ctx), { wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1" });
}

const createLoading = ref(false);
const moreLoading = ref(false);

const opCtx = {
  onDetail: (id: number) => void handleOpenDialog("detail", id),
  onEdit: (id: number) => void handleOpenDialog("update", id),
  onDelete: deleteRow,
  onTest: handleTestConnection,
};

// ====== useTable ======
const {
  columns, columnChecks, data, loading, pagination,
  getData, replaceSearchParams, resetSearchParams, handleSizeChange, handleCurrentChange,
  refreshData, refreshCreate, refreshUpdate, refreshRemove,
} = useTable({
  core: {
    apiFn: MysqlConfigAPI.listMysqlConfig,
    apiParams: { page_no: 1, page_size: 10 } as MysqlConfigPageQuery,
    columnsFactory: resolveStatusColumns<MysqlConfigTable>(() => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "name", label: "实例名称", minWidth: 120, showOverflowTooltip: true },
      { prop: "host", label: "主机地址", minWidth: 140, showOverflowTooltip: true },
      { prop: "port", label: "端口", width: 80 },
      { prop: "database_name", label: "数据库名", minWidth: 120, showOverflowTooltip: true },
      { prop: "username", label: "用户名", width: 100 },
      { prop: "password", label: "密码", width: 80, formatter: () => "****" },
      { prop: "db_model", label: "数据库模型", width: 110, tag: { map: { "local": { type: "primary", text: "本地" }, "cloud": { type: "success", text: "云数据库" }, "oceanbase": { type: "warning", text: "OceanBase" } } } },
      { prop: "charset", label: "字符集", width: 100 },
      { prop: "pool_size", label: "连接池", width: 80 },
      { prop: "max_overflow", label: "溢出连接", width: 90 },
      { prop: "remark", label: "备注", minWidth: 120, showOverflowTooltip: true },
      { prop: "created_time", label: "创建时间", width: 168, showOverflowTooltip: true },
      { prop: "operation", label: "操作", width: 220, fixed: "right", align: "center", formatter: (row: MysqlConfigTable) => formatOperationCell(row, opCtx) },
    ]),
  },
});

// ====== 搜索处理 ======
function handleSearch() { replaceSearchParams(searchForm.value); getData(); }
function handleReset() {
  searchForm.value = { name: undefined, host: undefined, status: undefined };
  resetSearchParams();
}

// ====== CRUD 弹窗 ======
const initialFormData: MysqlConfigForm = {
  id: undefined, name: undefined, host: "localhost", port: 3306,
  database_name: undefined, username: undefined, password: undefined,
  pool_size: 5, max_overflow: 10, db_model: "local", charset: "utf8mb4",
  status: 0, remark: undefined,
};

const formData = ref<MysqlConfigForm>({ ...initialFormData });
const { dialogVisible } = useCrudDialog();
const detailFormData = ref<MysqlConfigTable>({});
const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const formRenderKey = ref(0);

const rules = reactive({
  name: [{ required: true, message: "请输入实例名称", trigger: "blur" }],
  host: [{ required: true, message: "请输入主机地址", trigger: "blur" }],
  database_name: [{ required: true, message: "请输入数据库名", trigger: "blur" }],
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
});

const { submitLoading, handleCloseDialog, handleOpenDialog, handleSubmit } = useCrudForm<MysqlConfigForm>({
  formData,
  initialFormData,
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: MysqlConfigAPI.detailMysqlConfig,
  createApi: MysqlConfigAPI.createMysqlConfig,
  updateApi: MysqlConfigAPI.updateMysqlConfig,
  titles: { create: "新增 MySQL 配置", update: "修改 MySQL 配置", detail: "MySQL 配置详情" },
  detailFormData,
  onCreateSuccess: async () => { await refreshCreate(); },
  onUpdateSuccess: async () => { await refreshUpdate(); },
});

const formItems = computed<FormItem[]>(() => [
  { label: "实例名称", key: "name", type: "input", span: 12, props: { placeholder: "请输入实例名称" } },
  { label: "主机地址", key: "host", type: "input", span: 12, props: { placeholder: "请输入主机地址" } },
  { label: "端口", key: "port", type: "input-number", span: 12, props: { min: 1, max: 65535 } },
  { label: "数据库名", key: "database_name", type: "input", span: 12, props: { placeholder: "请输入数据库名" } },
  { label: "用户名", key: "username", type: "input", span: 12, props: { placeholder: "请输入用户名" } },
  { label: "密码", key: "password", type: "custom", span: 12 },
  { label: "数据库模型", key: "db_model", type: "select", span: 12, props: { placeholder: "请选择数据库模型", options: dbModelOptions.value } },
  { label: "字符集", key: "charset", type: "input", span: 12, props: { placeholder: "请输入字符集" } },
  { label: "连接池大小", key: "pool_size", type: "input-number", span: 12, props: { min: 1, max: 100 } },
  { label: "最大溢出连接", key: "max_overflow", type: "input-number", span: 12, props: { min: 0, max: 200 } },
  { label: "状态", key: "status", type: "custom", span: 12 },
  { label: "备注", key: "remark", type: "input", span: 24, props: { placeholder: "请输入备注", maxlength: 500 } },
]);

const detailItems: import("@/components/others/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "实例名称", prop: "name" },
  { label: "主机地址", prop: "host" },
  { label: "端口", prop: "port" },
  { label: "数据库名", prop: "database_name" },
  { label: "用户名", prop: "username" },
  { label: "密码", prop: "password" },
  { label: "数据库模型", prop: "db_model" },
  { label: "字符集", prop: "charset" },
  { label: "连接池大小", prop: "pool_size" },
  { label: "最大溢出连接", prop: "max_overflow" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "禁用" } } } },
  { label: "备注", prop: "remark", span: 4 },
];

async function handleAdd() {
  createLoading.value = true;
  try { await handleOpenDialog("create"); } finally { createLoading.value = false; }
}

// ====== 删除 ======
async function deleteRow(id: number) {
  await confirmDelete();
  await MysqlConfigAPI.deleteMysqlConfig([id]);
  faTableRef.value?.elTableRef?.clearSelection();
  await refreshRemove();
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return;
  await confirmBatchDelete(selectedIds.value.length);
  batchDeleting.value = true;
  try {
    await MysqlConfigAPI.deleteMysqlConfig(selectedIds.value);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } finally { batchDeleting.value = false; }
}

async function handleMoreClick(action: string) {
  if (!selectedIds.value.length) return;
  moreLoading.value = true;
  try {
    const status = action === "enable" ? 0 : 1;
    await MysqlConfigAPI.batchMysqlConfig({ ids: selectedIds.value, status });
    ElMessage.success(action === "enable" ? "已启用" : "已禁用");
    refreshData();
  } finally { moreLoading.value = false; }
}

// ====== 测试连接 ======
async function handleTestConnection(id: number) {
  try {
    await MysqlConfigAPI.testConnection(id);
    // 成功时由 Axios 拦截器弹出 SuccessResponse.msg 提示，此处无需重复
  } catch {
    // 失败时由 Axios 拦截器弹出 ErrorResponse.msg 提示
  }
}
</script>
