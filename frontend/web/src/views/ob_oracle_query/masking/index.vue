<!-- 敏感字段脱敏管理 -->
<template>
  <div class="masking-container">
    <div class="masking-layout">
      <!-- 左侧：脱敏规则管理 -->
      <el-card class="masking-left">
        <template #header>
          <div class="flex justify-between items-center">
            <span class="text-lg font-bold">脱敏规则</span>
            <el-button type="primary" @click="showRuleDialog()">
              <el-icon><Plus /></el-icon>新增规则
            </el-button>
          </div>
        </template>

        <el-table :data="rules" v-loading="rulesLoading" size="small">
          <el-table-column prop="rule_type" label="类型" width="60" />
          <el-table-column prop="rule_desc" label="描述" width="140" show-overflow-tooltip />
          <el-table-column prop="rule_regex" label="正则表达式" min-width="200" show-overflow-tooltip />
          <el-table-column prop="hide_group" label="隐藏组" width="70" align="center" />
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button type="primary" link @click="showRuleDialog(row)">编辑</el-button>
              <el-button type="danger" link @click="handleDeleteRule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 右侧：脱敏字段配置 -->
      <el-card class="masking-right">
        <template #header>
          <div class="flex justify-between items-center">
            <span class="text-lg font-bold">脱敏字段配置</span>
            <div class="flex items-center gap-2">
              <el-select v-model="selectedConfigId" placeholder="选择数据源" clearable style="width: 200px" @change="loadColumns">
                <el-option v-for="c in configList" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
              <el-button type="primary" @click="showColumnDialog()">
                <el-icon><Plus /></el-icon>添加字段
              </el-button>
            </div>
          </div>
        </template>

        <el-table :data="columns" v-loading="columnsLoading" size="small">
          <el-table-column prop="table_schema" label="Schema" width="100" />
          <el-table-column prop="table_name" label="表名" width="120" show-overflow-tooltip />
          <el-table-column prop="column_name" label="列名" width="120" show-overflow-tooltip />
          <el-table-column label="脱敏规则" width="140">
            <template #default="{ row }">
              {{ getRuleName(row.rule_type) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.active" @change="handleToggleColumn(row)" :loading="row._toggling" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button type="primary" link @click="showColumnDialog(row)">编辑</el-button>
              <el-button type="danger" link @click="handleDeleteColumn(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 规则对话框 -->
    <el-dialog v-model="ruleDialogVisible" :title="ruleForm.id ? '编辑规则' : '新增规则'" width="500px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则类型" required>
          <el-input-number v-model="ruleForm.rule_type" :min="1" :disabled="!!ruleForm.id" style="width: 100%" />
        </el-form-item>
        <el-form-item label="规则描述" required>
          <el-input v-model="ruleForm.rule_desc" placeholder="如：手机号脱敏" />
        </el-form-item>
        <el-form-item label="正则表达式" required>
          <el-input v-model="ruleForm.rule_regex" placeholder='如：^(\d{3})(\d{4})(\d{4})$' />
        </el-form-item>
        <el-form-item label="隐藏分组" required>
          <el-input-number v-model="ruleForm.hide_group" :min="1" style="width: 100%" />
          <div class="text-xs text-gray-500 mt-1">正则中第几个分组用 **** 替换（从1开始）</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitRule" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 字段配置对话框 -->
    <el-dialog v-model="columnDialogVisible" :title="columnForm.id ? '编辑字段配置' : '添加脱敏字段'" width="500px">
      <el-form :model="columnForm" label-width="100px">
        <el-form-item label="数据源" required>
          <el-select v-model="columnForm.config_id" placeholder="请选择数据源" style="width: 100%" :disabled="!!columnForm.id">
            <el-option v-for="c in configList" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Schema">
          <el-input v-model="columnForm.table_schema" placeholder="* 表示所有" />
        </el-form-item>
        <el-form-item label="表名">
          <el-input v-model="columnForm.table_name" placeholder="* 表示所有" />
        </el-form-item>
        <el-form-item label="列名" required>
          <el-input v-model="columnForm.column_name" placeholder="如：phone" />
        </el-form-item>
        <el-form-item label="脱敏规则" required>
          <el-select v-model="columnForm.rule_type" placeholder="请选择规则" style="width: 100%">
            <el-option v-for="r in rules" :key="r.rule_type" :label="`${r.rule_type} - ${r.rule_desc}`" :value="r.rule_type" />
          </el-select>
        </el-form-item>
        <el-form-item label="激活">
          <el-switch v-model="columnForm.active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="columnDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitColumn" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { request } from '@utils'

defineOptions({ name: 'DataMasking', inheritAttrs: false })

const getErrMsg = (e: any, fallback = '操作失败') => e?.response?.data?.msg || fallback

// ===== 数据源列表 =====
const configList = ref<Array<{ id: number; name: string }>>([])
const selectedConfigId = ref<number | null>(null)

const loadConfigs = async () => {
  try {
    const res = await request.get('/system/ob_oracle_config/list', {
      params: { page_no: 1, page_size: 100, status: 0 }
    })
    configList.value = res.data.data?.items || []
  } catch {
    ElMessage.error('加载数据源列表失败')
  }
}

// ===== 脱敏规则 =====
const rules = ref<any[]>([])
const rulesLoading = ref(false)

const loadRules = async () => {
  rulesLoading.value = true
  try {
    const res = await request.get('/ob_oracle_query/masking/rules', {
      params: { page_no: 1, page_size: 100 }
    })
    rules.value = res.data.data?.items || []
  } catch {
    ElMessage.error('加载脱敏规则失败')
  } finally {
    rulesLoading.value = false
  }
}

const getRuleName = (ruleType: number) => {
  const rule = rules.value.find(r => r.rule_type === ruleType)
  return rule ? `${rule.rule_type} - ${rule.rule_desc}` : `类型${ruleType}`
}

// 规则对话框
const ruleDialogVisible = ref(false)
const ruleForm = ref({ id: null as number | null, rule_type: 1, rule_regex: '', hide_group: 2, rule_desc: '' })

const showRuleDialog = (row?: any) => {
  if (row) {
    ruleForm.value = { id: row.id, rule_type: row.rule_type, rule_regex: row.rule_regex, hide_group: row.hide_group, rule_desc: row.rule_desc }
  } else {
    ruleForm.value = { id: null, rule_type: 1, rule_regex: '', hide_group: 2, rule_desc: '' }
  }
  ruleDialogVisible.value = true
}

const submitting = ref(false)

const handleSubmitRule = async () => {
  if (!ruleForm.value.rule_desc || !ruleForm.value.rule_regex) {
    ElMessage.warning('请填写完整信息')
    return
  }
  submitting.value = true
  try {
    if (ruleForm.value.id) {
      await request.put(`/ob_oracle_query/masking/rules/${ruleForm.value.id}`, {
        rule_regex: ruleForm.value.rule_regex,
        hide_group: ruleForm.value.hide_group,
        rule_desc: ruleForm.value.rule_desc,
      })
    } else {
      await request.post('/ob_oracle_query/masking/rules', ruleForm.value)
    }
    ruleDialogVisible.value = false
    await loadRules()
  } catch (error: any) {
    ElMessage.error(getErrMsg(error))
  } finally {
    submitting.value = false
  }
}

const handleDeleteRule = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除规则「${row.rule_desc}」？`, '提示', { type: 'warning' })
    await request.delete('/ob_oracle_query/masking/rules', { data: [row.id] })
    await loadRules()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error(getErrMsg(error, '删除失败'))
  }
}

// ===== 脱敏字段配置 =====
const columns = ref<any[]>([])
const columnsLoading = ref(false)

const loadColumns = async () => {
  columnsLoading.value = true
  try {
    const params: any = { page_no: 1, page_size: 100 }
    if (selectedConfigId.value) params.config_id = selectedConfigId.value
    const res = await request.get('/ob_oracle_query/masking/columns', { params })
    columns.value = (res.data.data?.items || []).map((c: any) => ({ ...c, _toggling: false }))
  } catch {
    ElMessage.error('加载脱敏字段配置失败')
  } finally {
    columnsLoading.value = false
  }
}

// 字段对话框
const columnDialogVisible = ref(false)
const columnForm = ref({
  id: null as number | null,
  config_id: null as number | null,
  table_schema: '*',
  table_name: '*',
  column_name: '',
  rule_type: null as number | null,
  active: true,
})

const showColumnDialog = (row?: any) => {
  if (row) {
    columnForm.value = {
      id: row.id, config_id: row.config_id, table_schema: row.table_schema,
      table_name: row.table_name, column_name: row.column_name,
      rule_type: row.rule_type, active: row.active,
    }
  } else {
    columnForm.value = {
      id: null, config_id: selectedConfigId.value, table_schema: '*',
      table_name: '*', column_name: '', rule_type: null, active: true,
    }
  }
  columnDialogVisible.value = true
}

const handleSubmitColumn = async () => {
  if (!columnForm.value.config_id || !columnForm.value.column_name || !columnForm.value.rule_type) {
    ElMessage.warning('请填写完整信息')
    return
  }
  submitting.value = true
  try {
    if (columnForm.value.id) {
      await request.put(`/ob_oracle_query/masking/columns/${columnForm.value.id}`, {
        table_schema: columnForm.value.table_schema,
        table_name: columnForm.value.table_name,
        column_name: columnForm.value.column_name,
        rule_type: columnForm.value.rule_type,
        active: columnForm.value.active,
      })
    } else {
      await request.post('/ob_oracle_query/masking/columns', columnForm.value)
    }
    columnDialogVisible.value = false
    await loadColumns()
  } catch (error: any) {
    ElMessage.error(getErrMsg(error))
  } finally {
    submitting.value = false
  }
}

const handleToggleColumn = async (row: any) => {
  row._toggling = true
  try {
    await request.put(`/ob_oracle_query/masking/columns/${row.id}`, { active: row.active })
  } catch (error: any) {
    row.active = !row.active
    ElMessage.error(getErrMsg(error, '切换失败'))
  } finally {
    row._toggling = false
  }
}

const handleDeleteColumn = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除字段「${row.column_name}」的脱敏配置？`, '提示', { type: 'warning' })
    await request.delete('/ob_oracle_query/masking/columns', { data: [row.id] })
    await loadColumns()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error(getErrMsg(error, '删除失败'))
  }
}

onMounted(async () => {
  await Promise.all([loadConfigs(), loadRules(), loadColumns()])
})
</script>

<style scoped>
.masking-container {
  padding: 20px;
}

.masking-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.masking-left {
  width: 560px;
  flex-shrink: 0;
}

.masking-right {
  flex: 1;
  min-width: 0;
}
</style>
