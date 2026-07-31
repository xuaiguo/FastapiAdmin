<!-- OB Oracle SQL 查询 -->
<template>
  <div class="fa-full-height flex flex-col">
    <!-- 顶部：数据源 + 控制栏 -->
    <div class="flex items-center gap-3 px-4 py-2 border-b">
      <span class="text-sm font-medium">数据源：</span>
      <ElSelect v-model="selectedConfigId" style="width: 280px">
        <ElOption v-for="c in configList" :key="c.id" :label="c.name" :value="c.id" />
      </ElSelect>
      <ElInputNumber v-model="maxRows" :min="1" :max="10000" :step="100" style="width: 140px" />
      <span class="text-xs text-gray-500">最大行数</span>
      <span class="text-red-500 text-xs">[{{ moduleName }}] 提醒：SQL 语句执行不能超过 15 秒</span>
      <ElButton type="primary" :loading="executing" @click="handleExecute">
        <ElIcon class="mr-1"><CaretRight /></ElIcon>执行
      </ElButton>
      <ElButton @click="openHistory">
        <ElIcon class="mr-1"><Clock /></ElIcon>历史
      </ElButton>
    </div>

    <!-- SQL 编辑器 -->
    <div class="flex-1 min-h-0 p-4 pb-2">
      <Codemirror
        ref="cmRef"
        v-model:value="sqlText"
        :options="cmOptions"
        border
        height="100%"
        width="100%"
        placeholder="输入 SQL 查询语句（仅支持 SELECT）..."
      />
    </div>

    <!-- 结果区域 -->
    <div class="border-t p-4 pt-2" style="min-height: 200px; max-height: 50vh; overflow: auto">
      <!-- 状态栏 -->
      <div class="flex items-center gap-4 mb-2 text-sm">
        <span v-if="result" class="text-gray-600">
          返回 <strong>{{ result.total }}</strong> 行
          <span v-if="result.truncated" class="text-orange-500 ml-1">（已截断）</span>
        </span>
        <span v-if="result" class="text-gray-500">耗时 {{ result.elapsed_ms }} ms</span>
        <span v-if="errorMsg" class="text-red-500">{{ errorMsg }}</span>
        <template v-if="result && result.columns.length > 0">
          <ElButton size="small" @click="exportCSV">导出 CSV</ElButton>
          <ElButton size="small" @click="exportExcel">导出 Excel</ElButton>
        </template>
      </div>

      <!-- 结果表格 -->
      <ElTable
        v-if="result && result.columns.length > 0"
        :data="tableData"
        border
        stripe
        size="small"
        max-height="400"
        style="width: 100%"
      >
        <ElTableColumn
          v-for="col in result.columns"
          :key="col"
          :prop="col"
          :label="col"
          :min-width="colWidth(col)"
          show-overflow-tooltip
        />
      </ElTable>

      <ElEmpty v-else-if="!result && !errorMsg" description="输入 SQL 后点击执行" />
    </div>

    <!-- 历史抽屉 -->
    <ElDrawer v-model="historyVisible" title="查询历史" size="600px" direction="rtl">
      <div class="flex items-center gap-2 mb-4">
        <ElSelect v-model="historyFilter" placeholder="全部状态" clearable style="width: 120px" @change="loadHistory">
          <ElOption label="成功" :value="0" />
          <ElOption label="失败" :value="1" />
        </ElSelect>
        <ElButton size="small" type="danger" plain @click="handleClearHistory">清空历史</ElButton>
      </div>

      <div v-if="historyLoading" class="text-center py-8 text-gray-400">加载中...</div>
      <div v-else-if="historyList.length === 0" class="text-center py-8 text-gray-400">暂无历史记录</div>
      <div v-else class="space-y-3">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="border rounded-lg p-3 hover:bg-gray-50 cursor-pointer"
          @click="loadSqlFromHistory(item.sql)"
        >
          <div class="flex items-center justify-between mb-1">
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-400">{{ item.created_time }}</span>
              <span v-if="item.created_by" class="text-xs text-blue-500">{{ item.created_by.nickname || item.created_by.username }}</span>
            </div>
            <div class="flex items-center gap-2">
              <ElTag :type="item.status === 0 ? 'success' : 'danger'" size="small">
                {{ item.status === 0 ? '成功' : '失败' }}
              </ElTag>
              <span v-if="item.elapsed_ms != null" class="text-xs text-gray-400">{{ item.elapsed_ms }}ms</span>
              <span v-if="item.row_count != null" class="text-xs text-gray-400">{{ item.row_count }}行</span>
              <ElButton size="small" text type="danger" @click.stop="handleDeleteHistory(item.id)">
                <ElIcon><Delete /></ElIcon>
              </ElButton>
            </div>
          </div>
          <div class="text-sm font-mono text-gray-700 whitespace-pre-wrap break-all line-clamp-3">{{ item.sql }}</div>
          <div v-if="item.error_msg" class="text-xs text-red-400 mt-1 line-clamp-2">{{ item.error_msg }}</div>
        </div>
      </div>

      <div v-if="historyList.length > 0" class="flex justify-center mt-4">
        <ElPagination
          v-model:current-page="historyPage"
          :page-size="10"
          :total="historyTotal"
          layout="prev, pager, next"
          @current-change="loadHistory"
        />
      </div>
    </ElDrawer>
  </div>
</template>

<script setup lang="ts">
import "codemirror/mode/sql/sql.js";
import "codemirror/theme/dracula.css";
import "codemirror/addon/hint/show-hint.css";
import "codemirror/addon/hint/sql-hint.js";
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { CaretRight, Clock, Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import Codemirror from "codemirror-editor-vue3";
import type { EditorConfiguration } from "codemirror";
import ObOracleQueryAPI, {
  type ObOracleConfigOption,
  type ObOracleQueryResult,
  type QueryHistoryRow,
} from "@/api/ob_oracle_query/obOracleQuery";

defineOptions({ name: "ObOracleQuery", inheritAttrs: false });

// ====== 路由信息 ======
const route = useRoute();
const moduleName = computed(() => {
  // 直接使用路由名称
  return route.name as string;
});

// ====== 数据源 ======
const configList = ref<ObOracleConfigOption[]>([]);
const selectedConfigId = ref<number>(1);

onMounted(async () => {
  try {
    const res = await ObOracleQueryAPI.listObOracleConfigs({
      module_name: moduleName.value
    });
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

// ====== SQL 编辑器 ======
const cmRef = ref();
const sqlText = ref("");
const maxRows = ref(1000);

const cmOptions: EditorConfiguration = {
  mode: "text/x-sql",
  theme: "dracula",
  lineNumbers: true,
  lineWrapping: true,
  matchBrackets: true,
  autoCloseBrackets: true,
  extraKeys: {
    "Ctrl-Space": "autocomplete",
    "Ctrl-Enter": () => handleExecute(),
  },
};

// ====== 执行 ======
const executing = ref(false);
const result = ref<ObOracleQueryResult | null>(null);
const errorMsg = ref("");

async function handleExecute() {
  const sql = sqlText.value.trim();
  if (!sql) {
    errorMsg.value = "请输入 SQL 语句";
    return;
  }
  executing.value = true;
  errorMsg.value = "";
  result.value = null;
  try {
    const res = await ObOracleQueryAPI.executeSql({
      config_id: selectedConfigId.value,
      sql,
      max_rows: maxRows.value,
      module_name: moduleName.value,
    });
    const resData = (res as any)?.data;
    const payload = resData?.data || resData;
    if (resData?.code === 200 || resData?.success) {
      result.value = payload as ObOracleQueryResult;
    } else {
      errorMsg.value = resData?.msg || "查询失败";
    }
  } catch (e: any) {
    errorMsg.value = e?.message || "请求失败";
  } finally {
    executing.value = false;
  }
}

// ====== 导出功能 ======
function exportCSV() {
  if (!result.value || result.value.columns.length === 0) return;
  const { columns, rows } = result.value;
  const csvContent = [
    columns.join(","),
    ...rows.map((row) =>
      row.map((cell) => {
        const val = cell == null ? "" : String(cell);
        return val.includes(",") || val.includes('"') || val.includes("\n")
          ? `"${val.replace(/"/g, '""')}"`
          : val;
      }).join(",")
    ),
  ].join("\n");
  const bom = "﻿";
  const blob = new Blob([bom + csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `sql_query_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, "")}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function exportExcel() {
  if (!result.value || result.value.columns.length === 0) return;
  const XLSX = await import("xlsx");
  const { columns, rows } = result.value;
  const data = [columns, ...rows];
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "查询结果");
  XLSX.writeFile(wb, `sql_query_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, "")}.xlsx`);
}

// ====== 动态表格 ======
const tableData = computed(() => {
  if (!result.value) return [];
  const { columns, rows } = result.value;
  return rows.map((row) => {
    const obj: Record<string, any> = {};
    columns.forEach((col, idx) => {
      obj[col] = row[idx];
    });
    return obj;
  });
});

function colWidth(col: string): number {
  if (col.toUpperCase().includes("SQL") || col.toUpperCase().includes("QUERY")) return 250;
  if (col.toUpperCase().includes("TIME") || col.toUpperCase().includes("DATE")) return 170;
  if (col.toUpperCase().includes("IP")) return 140;
  return 120;
}

// ====== 查询历史 ======
const historyVisible = ref(false);
const historyLoading = ref(false);
const historyList = ref<QueryHistoryRow[]>([]);
const historyPage = ref(1);
const historyTotal = ref(0);
const historyFilter = ref<number | undefined>(undefined);

function openHistory() {
  historyVisible.value = true;
  historyPage.value = 1;
  loadHistory();
}

async function loadHistory() {
  historyLoading.value = true;
  try {
    const res = await ObOracleQueryAPI.listHistory({
      page_no: historyPage.value,
      page_size: 10,
      status: historyFilter.value,
    });
    const resData = (res as any)?.data;
    const payload = resData?.data || resData || {};
    historyList.value = payload.items || payload.rows || [];
    historyTotal.value = payload.total || 0;
  } catch {
    historyList.value = [];
  } finally {
    historyLoading.value = false;
  }
}

function loadSqlFromHistory(sql: string) {
  sqlText.value = sql;
  historyVisible.value = false;
}

async function handleDeleteHistory(id: number) {
  try {
    await ObOracleQueryAPI.deleteHistory([id]);
    ElMessage.success("删除成功");
    loadHistory();
  } catch {
    ElMessage.error("删除失败");
  }
}

async function handleClearHistory() {
  try {
    await ElMessageBox.confirm("确认清空所有查询历史？", "提示", { type: "warning" });
    await ObOracleQueryAPI.clearHistory();
    ElMessage.success("清空成功");
    loadHistory();
  } catch {
    // 取消操作
  }
}
</script>
