<template>
  <div class="ob-module-container">
    <div class="ob-layout">
      <!-- 父菜单配置区域（左侧） -->
      <el-card class="ob-left">
        <template #header>
          <div class="flex justify-between items-center">
            <span class="text-lg font-bold">父菜单配置</span>
            <el-button type="primary" @click="showAddParentMenuDialog">
              <el-icon><Plus /></el-icon>添加父菜单
            </el-button>
          </div>
        </template>

        <el-table :data="parentMenus" v-loading="loadingParentMenus">
          <el-table-column prop="menu_id" label="菜单ID" width="100" />
          <el-table-column prop="menu_name" label="父菜单名称" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button
                type="danger"
                link
                @click="handleDeleteParentMenu(row.menu_id)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 模块列表区域（右侧） -->
      <el-card class="ob-right">
      <template #header>
        <div class="flex justify-between items-center">
          <span class="text-lg font-bold">OB 模块管理</span>
          <el-button type="primary" @click="showAddModuleDialog">
            <el-icon><Plus /></el-icon>手动添加模块
          </el-button>
        </div>
      </template>

      <el-table :data="pagedModules" v-loading="loadingModules">
        <el-table-column prop="module_name" label="模块名称" width="200" />
        <el-table-column prop="module_label" label="显示名称" width="150" />
        <el-table-column prop="parent_menu_name" label="所属父菜单" width="150" />
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.source_type === 1 ? 'success' : 'warning'">
              {{ row.source_type === 1 ? '菜单提取' : '手动添加' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="已分配数据源" min-width="200">
          <template #default="{ row }">
            <div v-if="row.config_ids && row.config_ids.length > 0">
              <el-tag
                v-for="configId in row.config_ids"
                :key="configId"
                class="mr-2 mb-1"
                type="info"
              >
                {{ getConfigName(configId) }}
              </el-tag>
            </div>
            <el-text v-else type="info">未分配</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="showAllocateDialog(row)">
              分配数据源
            </el-button>
            <template v-if="row.source_type === 2">
              <el-button type="primary" link @click="handleViewModule(row)">
                查看
              </el-button>
              <el-button type="primary" link @click="showEditModuleDialog(row)">
                编辑
              </el-button>
              <el-button type="danger" link :loading="deletingModule" @click="handleDeleteModule(row)">
                删除
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="modules.length"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>
    </div><!-- .ob-layout -->

    <!-- 添加父菜单对话框 -->
    <el-dialog
      v-model="parentMenuDialogVisible"
      title="添加父菜单"
      width="500px"
    >
      <el-form :model="parentMenuForm" label-width="100px">
        <el-form-item label="选择菜单" required>
          <el-select
            v-model="parentMenuForm.menu_id"
            placeholder="请选择父菜单"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="menu in availableMenus"
              :key="menu.id"
              :label="menu.title"
              :value="menu.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="parentMenuDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddParentMenu" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 手动添加/编辑模块对话框 -->
    <el-dialog
      v-model="moduleDialogVisible"
      :title="moduleForm.id ? '编辑模块' : '手动添加模块'"
      width="500px"
    >
      <el-form :model="moduleForm" label-width="100px">
        <el-form-item label="模块名称" required>
          <el-input
            v-model="moduleForm.module_name"
            placeholder="如 ObOracleQuery"
            :disabled="!!moduleForm.id"
          />
        </el-form-item>
        <el-form-item label="显示名称" required>
          <el-input
            v-model="moduleForm.module_label"
            placeholder="如 SQL查询"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitModule" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 模块详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="模块详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="模块名称">{{ detailData.module_name }}</el-descriptions-item>
        <el-descriptions-item label="显示名称">{{ detailData.module_label }}</el-descriptions-item>
        <el-descriptions-item label="来源">手动添加</el-descriptions-item>
        <el-descriptions-item label="已分配数据源">
          <template v-if="detailData.config_ids && detailData.config_ids.length > 0">
            <el-tag v-for="cid in detailData.config_ids" :key="cid" class="mr-2" type="info">
              {{ getConfigName(cid) }}
            </el-tag>
          </template>
          <el-text v-else type="info">未分配</el-text>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 分配数据源对话框 -->
    <el-dialog
      v-model="allocateDialogVisible"
      title="分配数据源"
      width="600px"
    >
      <el-form label-width="100px">
        <el-form-item label="模块名称">
          <el-text>{{ currentModule?.module_name }}</el-text>
        </el-form-item>
        <el-form-item label="选择数据源" required>
          <el-select
            v-model="allocateForm.config_ids"
            multiple
            placeholder="请选择数据源（最少1个）"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="config in configs"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="allocateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAllocate" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { request } from '@utils'

// 类型定义
interface ParentMenu {
  menu_id: number
  menu_name: string
}

interface Module {
  id: number
  module_name: string
  module_label: string
  source_type: number
  status: number
  config_ids: number[]
  parent_menu_name: string
}

interface Config {
  id: number
  name: string
}

interface Menu {
  id: number
  title: string
}

// 响应式数据
const loadingParentMenus = ref(false)
const loadingModules = ref(false)
const submitting = ref(false)
const deletingModule = ref(false)

// 统一提取后端错误消息
const getErrMsg = (e: any, fallback = '操作失败') =>
  e?.response?.data?.msg || fallback

const parentMenus = ref<ParentMenu[]>([])
const modules = ref<Module[]>([])
const configs = ref<Config[]>([])
const allMenus = ref<Menu[]>([])

// 对话框可见性
const parentMenuDialogVisible = ref(false)
const moduleDialogVisible = ref(false)
const allocateDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const detailData = ref<Module>({
  id: 0, module_name: '', module_label: '',
  source_type: 2, status: 0, config_ids: [], parent_menu_name: ''
})

// 表单数据
const parentMenuForm = ref({
  menu_id: null as number | null
})

const moduleForm = ref({
  id: null as number | null,
  module_name: '',
  module_label: ''
})

const allocateForm = ref({
  config_ids: [] as number[]
})

const currentModule = ref<Module | null>(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

const pagedModules = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return modules.value.slice(start, start + pageSize.value)
})

// 计算属性：可用的菜单（排除已配置的）
const availableMenus = computed(() => {
  const configuredIds = parentMenus.value.map(pm => pm.menu_id)
  return allMenus.value.filter(menu => !configuredIds.includes(menu.id))
})

// 获取配置名称
const getConfigName = (configId: number): string => {
  const config = configs.value.find(c => c.id === configId)
  return config ? config.name : `配置${configId}`
}

// 加载父菜单列表
const loadParentMenus = async () => {
  loadingParentMenus.value = true
  try {
    const res = await request.get('/system/ob_module/parent_menus')
    parentMenus.value = res.data.data || []
  } catch (error) {
    ElMessage.error('加载父菜单列表失败')
  } finally {
    loadingParentMenus.value = false
  }
}

// 加载模块列表
const loadModules = async () => {
  loadingModules.value = true
  try {
    const res = await request.get('/system/ob_module/list')
    modules.value = res.data.data || []
    currentPage.value = 1
  } catch (error) {
    ElMessage.error('加载模块列表失败')
  } finally {
    loadingModules.value = false
  }
}

// 加载数据源列表
const loadConfigs = async () => {
  try {
    const res = await request.get('/system/ob_oracle_config/list', {
      params: { page_no: 1, page_size: 100, status: 0 }
    })
    configs.value = res.data.data?.items || []
  } catch (error) {
    ElMessage.error('加载数据源列表失败')
  }
}

// 加载所有菜单
const loadAllMenus = async () => {
  try {
    const res = await request.get('/system/menu/tree')
    const tree = res.data.data || []
    // 只取一级目录菜单（type=1）作为可选父菜单
    allMenus.value = tree
      .filter((node: any) => node.type === 1)
      .map((node: any) => ({ id: node.id, title: node.title || node.name }))
  } catch (error) {
    ElMessage.error('加载菜单列表失败')
  }
}

// 显示添加父菜单对话框
const showAddParentMenuDialog = () => {
  parentMenuForm.value.menu_id = null
  parentMenuDialogVisible.value = true
}

// 添加父菜单
const handleAddParentMenu = async () => {
  if (!parentMenuForm.value.menu_id) {
    ElMessage.warning('请选择菜单')
    return
  }

  submitting.value = true
  try {
    await request.post('/system/ob_module/parent_menus', null, {
      params: { menu_id: parentMenuForm.value.menu_id }
    })
    parentMenuDialogVisible.value = false
    await loadParentMenus()
  } catch (error: any) {
    ElMessage.error(getErrMsg(error, '添加失败'))
  } finally {
    submitting.value = false
  }
}

// 删除父菜单
const handleDeleteParentMenu = async (menuId: number) => {
  try {
    await ElMessageBox.confirm('删除后该父菜单下的模块将不再自动提取，是否继续？', '提示', {
      type: 'warning'
    })

    await request.delete(`/system/ob_module/parent_menus/${menuId}`)
    await loadParentMenus()
    await loadModules()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 显示添加模块对话框
const showAddModuleDialog = () => {
  moduleForm.value = {
    id: null,
    module_name: '',
    module_label: ''
  }
  moduleDialogVisible.value = true
}

// 编辑模块
const showEditModuleDialog = (module: Module) => {
  moduleForm.value = {
    id: module.id,
    module_name: module.module_name,
    module_label: module.module_label
  }
  moduleDialogVisible.value = true
}

// 提交（新增或编辑）
const handleSubmitModule = async () => {
  if (!moduleForm.value.module_name || !moduleForm.value.module_label) {
    ElMessage.warning('请填写模块名称和显示名称')
    return
  }

  submitting.value = true
  try {
    if (moduleForm.value.id) {
      // 编辑模式
      await request.put(`/system/ob_module/update/${moduleForm.value.id}`, {
        module_label: moduleForm.value.module_label
      })
    } else {
      // 新增模式
      await request.post('/system/ob_module/add', {
        module_name: moduleForm.value.module_name,
        module_label: moduleForm.value.module_label
      })
    }
    moduleDialogVisible.value = false
    await loadModules()
  } catch (error: any) {
    ElMessage.error(getErrMsg(error, '操作失败'))
  } finally {
    submitting.value = false
  }
}

// 查看模块详情
const handleViewModule = async (module: Module) => {
  try {
    const res = await request.get(`/system/ob_module/detail/${module.id}`)
    detailData.value = res.data.data
    detailDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(getErrMsg(error, '加载详情失败'))
  }
}

// 删除模块
const handleDeleteModule = async (module: Module) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模块「${module.module_label}」吗？删除后将同时清除已分配的数据源。`,
      '提示',
      { type: 'warning' }
    )
    deletingModule.value = true
    await request.delete('/system/ob_module/delete', { data: [module.id] })
    await loadModules()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(getErrMsg(error, '删除失败'))
    }
  } finally {
    deletingModule.value = false
  }
}

// 显示分配数据源对话框
const showAllocateDialog = (module: Module) => {
  currentModule.value = module
  allocateForm.value.config_ids = [...(module.config_ids || [])]
  allocateDialogVisible.value = true
}

// 分配数据源
const handleAllocate = async () => {
  if (allocateForm.value.config_ids.length < 1) {
    ElMessage.warning('最少选择1个数据源')
    return
  }

  submitting.value = true
  try {
    await request.post('/system/ob_module/allocate_configs', {
      module_name: currentModule.value!.module_name,
      config_ids: allocateForm.value.config_ids
    })
    allocateDialogVisible.value = false
    await loadModules()
  } catch (error: any) {
    ElMessage.error(getErrMsg(error, '分配失败'))
  } finally {
    submitting.value = false
  }
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadParentMenus(),
    loadModules(),
    loadConfigs(),
    loadAllMenus()
  ])
})
</script>

<style scoped>
.ob-module-container {
  padding: 20px;
}

.ob-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.ob-left {
  width: 420px;
  flex-shrink: 0;
}

.ob-right {
  flex: 1;
  min-width: 0;
}

.mb-4 {
  margin-bottom: 16px;
}

.mr-2 {
  margin-right: 8px;
}

.mb-1 {
  margin-bottom: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
