<template>
  <div class="fa-full-height">
    <FaSearchBarWithAudit
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="businessSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :disabled-search="false"
      :default-expanded="false"
      @search="handleSearch"
      @reset="onResetSearch"
    />

    <ElCard
      shadow="hover"
      class="fa-table-card"
      :style="{ 'margin-top': showSearchBar ? '12px' : '0' }"
    >
      <FaTableHeader
        v-model:columns="columnChecks"
        v-model:showSearchBar="showSearchBar"
        :loading="loading"
        @refresh="refreshData"
      >
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_example:demo_single:create']"
            :perm-import="['module_example:demo_single:import']"
            :perm-export="['module_example:demo_single:export']"
            :perm-delete="['module_example:demo_single:delete']"
            :perm-patch="['module_example:demo_single:patch']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @import="openImport"
            @export="openExport"
            @delete="handleBatchDelete"
            @more="runBatchStatus"
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
      width="920px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @confirm="dialogVisible.type === 'detail' ? handleCloseDialog() : handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions :column="4" :data="detailFormData" :items="detailItems" max-height="70vh" />
      </template>
      <template v-else>
        <FaForm
          :key="formRenderKey"
          scrollbar
          max-height="70vh"
          ref="dataFormRef"
          v-model="formData"
          :items="dialogFormItems"
          :rules="rules"
          label-suffix=":"
          :label-width="100"
          label-position="right"
          :span="24"
          :gutter="16"
          :show-reset="false"
          :show-submit="false"
          class="crud-dialog-art-form"
        />
      </template>

      <template #footer>
        <div class="dialog-footer" style="padding-right: var(--el-dialog-padding-primary)">
          <ElButton @click="handleCloseDialog">取消</ElButton>
          <ElButton v-if="dialogVisible.type !== 'detail'" type="primary" @click="handleSubmit">
            确定
          </ElButton>
          <ElButton v-else type="primary" @click="handleCloseDialog">确定</ElButton>
        </div>
      </template>
    </FaDialog>

    <FaImportDialog
      v-model="importVisible"
      :content-config="importContentConfig"
      default-template-file-name="demo_single_import_template.xlsx"
      @upload="handleCrudImportUpload"
    />

    <FaExportDialog
      v-model="exportVisible"
      :content-config="exportContentConfig"
      :query-params="exportQueryParams"
      :page-data="data"
      :selection-data="selectedRows"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useAuth } from "@/hooks/core/useAuth";
import { renderTableOperationCell, type TableOperationAction } from "@/utils/table";
import { useTable } from "@/hooks/core/useTable";
import { useImportExport } from "@/hooks/core/useImportExport";
import { useCrudDialog } from "@/hooks/core/useCrudDialog";
import { useTableSelection } from "@/hooks/core/useTableSelection";
import { confirmDelete, confirmBatchDelete, confirmAction } from "@/hooks/core/useConfirm";
import { stripPaginationParams } from "@/utils/query";
import type { IContentConfig, IObject } from "@/components/modal/types";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { ColumnOption } from "@/types/component";
import GenDemoSingleAPI, {
  type GenDemoSingleForm,
  type GenDemoSinglePageQuery,
  type GenDemoSingleTable,
} from "@/api/module_example/demo_single";
import { ResultEnum } from "@/enums/api/result.enum";
import { ElMessage } from "element-plus";

defineOptions({
  name: "GenDemoSingle",
  inheritAttrs: false,
});

const { hasAuth } = useAuth();

// 常量定义
const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const createInitialFormData = (): GenDemoSingleForm => ({
  name: undefined,
  status: "0",
  description: undefined,
});

type GenDemoSingleSearchFormParams = {
  name?: string;
  status?: string;
} & AuditSearchFormParams;

const searchForm = ref<GenDemoSingleSearchFormParams>({
  name: undefined,
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: [],
  updated_time: [],
});

/** 搜索区域默认展开展示 */
const showSearchBar = ref(true);

const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

/** 业务搜索项（审计四字段由 FaSearchBarWithAudit 自动追加） */
const businessSearchItems = computed(() => [
  {
    label: "名称",
    key: "name",
    type: "input",
    placeholder: "请输入名称",
    clearable: true,
    span: 6,
  },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      options: STATUS_OPTIONS,
      clearable: true,
    },
    span: 6,
  },
]);

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<GenDemoSingleTable>();

const createLoading = ref(false);

const PK = "id" as const;

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  searchParams,
  getData,
  replaceSearchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData,
  refreshCreate,
  refreshUpdate,
  refreshRemove,
} = useTable({
  core: {
    apiFn: GenDemoSingleAPI.getGenDemoSingleList,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<GenDemoSingleTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "name", label: "名称", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "info", text: "停用" },
        },
      },
      { prop: "description", label: "备注/描述", minWidth: 120, showOverflowTooltip: true },
      { prop: "created_time", label: "创建时间", width: 168, showOverflowTooltip: true },
      { prop: "updated_time", label: "更新时间", width: 168, showOverflowTooltip: true },
      {
        prop: "created_by",
        label: "创建人",
        minWidth: 100,
        formatter: (row: GenDemoSingleTable) => row.created_by?.name ?? "—",
      },
      {
        prop: "updated_by",
        label: "更新人",
        minWidth: 100,
        formatter: (row: GenDemoSingleTable) => row.updated_by?.name ?? "—",
      },
      {
        prop: "operation",
        label: "操作",
        width: 220,
        fixed: "right",
        align: "right",
        formatter: (row: GenDemoSingleTable) => formatOperationCell(row),
      },
    ],
  },
});

const crudCols = computed(() =>
  columns.value.map((c: ColumnOption<GenDemoSingleTable>) => {
    const t = (c as { type?: string }).type;
    return {
      prop: c.prop,
      label: c.label,
      type: t === "selection" ? ("selection" as const) : ("default" as const),
      show: true,
    };
  })
);

const exportQueryParams = computed(() => {
  return stripPaginationParams(searchParams as Record<string, unknown>);
});

const importContentConfig = computed<IContentConfig>(() => ({
  permPrefix: "module_example:demo_single",
  cols: crudCols.value,
  indexAction: async () => ({}),
  importTemplate: () => GenDemoSingleAPI.downloadTemplateGenDemoSingle(),
}));

const exportContentConfig = computed(() => ({
  permPrefix: "module_example:demo_single",
  cols: crudCols.value,
  exportsBlobAction: async (params: IObject) => {
    const merged = {
      ...(exportQueryParams.value as unknown as Record<string, unknown>),
      ...params,
    } as unknown as GenDemoSinglePageQuery;
    const res = await GenDemoSingleAPI.exportGenDemoSingle(merged);
    return res.data as Blob;
  },
}));

const { dialogVisible } = useCrudDialog();

const detailFormData = ref<GenDemoSingleTable>({});

const detailItems: import("@/components/others/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "名称", prop: "name" },
  {
    label: "状态",
    prop: "status",
    tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } } },
  },
  { label: "备注/描述", prop: "description" },
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
  { label: "创建人", prop: "created_by.name" },
  { label: "更新人", prop: "updated_by.name" },
];

const formData = ref<GenDemoSingleForm>(createInitialFormData());

const rules = reactive({
  name: [{ required: false, message: "请填写名称", trigger: "blur" }],
  status: [{ required: true, message: "请填写是否启用(0:启用 1:禁用)", trigger: "blur" }],
  description: [{ required: false, message: "请填写备注/描述", trigger: "blur" }],
});

const dialogFormItems: FormItem[] = [
  { key: "name", label: "名称", type: "input", props: { placeholder: "请输入名称" } },
  {
    key: "status",
    label: "状态",
    type: "radiogroup",
    props: {
      options: [
        { label: "启用", value: 0 },
        { label: "停用", value: 1 },
      ],
    },
  },
  {
    key: "description",
    label: "描述",
    type: "input",
    props: {
      type: "textarea",
      rows: 4,
      maxlength: 100,
      showWordLimit: true,
      placeholder: "请输入描述",
    },
  },
];

const dataFormRef = ref<{
  resetFields: () => void;
  clearValidate: () => void;
  validate: (cb: (valid: boolean) => void) => void;
} | null>(null);
const submitLoading = ref(false);
const formRenderKey = ref(0);

const { importVisible, exportVisible, openImport, openExport } = useImportExport();

const handleSearch = async (params: GenDemoSingleSearchFormParams) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    name: params.name,
    status: params.status,
    created_id: params.created_id ?? undefined,
    updated_id: params.updated_id ?? undefined,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2
        ? params.created_time
        : undefined,
    updated_time:
      Array.isArray(params.updated_time) && params.updated_time.length === 2
        ? params.updated_time
        : undefined,
  } as Record<string, unknown>);
  getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    name: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: [],
    updated_time: [],
  };
  await resetSearchParams();
};

function buildRowActions(row: GenDemoSingleTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_example:demo_single:detail",
      run: () => void openDetailDialog(row),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_example:demo_single:update",
      run: () => void openEditDialog("edit", row),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_example:demo_single:delete",
      run: () => deleteRow(row),
    },
  ];
  return all.filter((a) => a.perm != null && hasAuth(a.perm));
}

function formatOperationCell(row: GenDemoSingleTable) {
  return renderTableOperationCell(buildRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

async function openDetailDialog(row: GenDemoSingleTable) {
  if (!row[PK]) return;
  const response = await GenDemoSingleAPI.getGenDemoSingleDetail(row[PK] as number);
  dialogVisible.type = "detail";
  dialogVisible.title = "详情";
  detailFormData.value = response.data.data ?? { ...row };
  dialogVisible.visible = true;
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await openEditDialog("add");
  } finally {
    createLoading.value = false;
  }
}

async function openEditDialog(type: "add" | "edit", row?: GenDemoSingleTable) {
  dialogVisible.type = type === "add" ? "create" : "update";
  if (type === "add") {
    dialogVisible.title = "新增";
    Object.assign(formData.value, createInitialFormData());
    formData.value[PK] = undefined;
    formRenderKey.value += 1;
  } else if (row?.[PK]) {
    dialogVisible.title = "修改";
    formRenderKey.value += 1;
    const response = await GenDemoSingleAPI.getGenDemoSingleDetail(row[PK] as number);
    Object.assign(formData.value, response.data.data);
  }
  dialogVisible.visible = true;
}

async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  Object.assign(formData.value, createInitialFormData());
}

async function handleCloseDialog() {
  dialogVisible.visible = false;
  await resetForm();
}

async function handleSubmit() {
  dataFormRef.value?.validate(async (valid: boolean) => {
    if (!valid) return;
    const submitData = { ...formData.value };
    const id = formData.value[PK] as number | undefined;
    try {
      if (id) {
        await GenDemoSingleAPI.updateGenDemoSingle(id, { [PK]: id, ...submitData });
        await refreshUpdate();
      } else {
        await GenDemoSingleAPI.createGenDemoSingle(submitData);
        await refreshCreate();
      }
      dialogVisible.visible = false;
      await resetForm();
    } catch (error: unknown) {
      console.error(error);
    }
  });
}

const deleteRow = async (row: GenDemoSingleTable) => {
  if (!row[PK]) return;
  try {
    await confirmDelete("确定删除该数据吗？此操作不可恢复！");
    await GenDemoSingleAPI.deleteGenDemoSingle([row[PK] as number]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
};

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(ids.length);
    batchDeleting.value = true;
    await GenDemoSingleAPI.deleteGenDemoSingle(ids);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  } finally {
    batchDeleting.value = false;
  }
}

async function runBatchStatus(status: number) {
  const ids = selectedIds.value;
  if (ids.length === 0) {
    ElMessage.warning("请先在列表中勾选数据");
    return;
  }
  try {
    await confirmAction(
      `确认对选中的 ${ids.length} 条数据${status === 0 ? "启用" : "停用"}？`,
      "批量设置"
    );
    await GenDemoSingleAPI.batchGenDemoSingle({ ids, status });
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  }
}

async function handleCrudImportUpload(formData: FormData) {
  try {
    const res = await GenDemoSingleAPI.importGenDemoSingle(formData);
    if (res.data.code === ResultEnum.SUCCESS) {
      ElMessage.success(res.data.msg || "导入成功");
      importVisible.value = false;
      await refreshData();
    }
  } catch (error) {
    console.error("[Import]", error);
  }
}

onMounted(() => {
  getData();
});
</script>

<style lang="scss" scoped></style>
