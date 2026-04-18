<template>
  <div class="case-management">
    <div class="case-list-panel">
      <el-card class="list-card">
        <template #header>
          <div class="card-header">
            <span>用例列表</span>
            <el-button type="primary" size="small" @click="createNewCase">
              <el-icon><Plus /></el-icon>
              新建
            </el-button>
          </div>
        </template>
        
        <div class="filter-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用例"
            clearable
            size="small"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select v-model="filterFolder" placeholder="目录" clearable size="small" @change="handleSearch">
            <el-option label="全部" :value="0" />
            <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
          </el-select>
          
          <el-select v-model="filterTag" placeholder="标签" clearable size="small" @change="handleSearch">
            <el-option label="全部" value="" />
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.name" />
          </el-select>
        </div>
        
        <div class="case-list-container" v-loading="loading">
          <div
            v-for="item in cases"
            :key="item.id"
            class="case-item"
            :class="{ active: selectedCase?.id === item.id }"
            @click="selectCase(item)"
          >
            <div class="case-name">
              <el-icon v-if="item.is_template" style="color: #e6a23c; margin-right: 4px"><Star /></el-icon>
              {{ item.name }}
            </div>
            <div class="case-meta">
              <el-tag v-if="item.case_type" size="small" type="info">{{ item.case_type }}</el-tag>
              <span v-if="item.folder_id" class="folder">{{ getFolderName(item.folder_id) }}</span>
            </div>
            <div class="case-tags">
              <el-tag
                v-for="tag in item.tags?.slice(0, 2)"
                :key="tag.id"
                size="small"
                :color="tag.color"
                style="margin-right: 4px"
              >
                {{ tag.name }}
              </el-tag>
              <el-tag v-if="item.tags?.length > 2" size="small" type="info">
                +{{ item.tags.length - 2 }}
              </el-tag>
            </div>
            <div class="case-actions">
              <el-button type="primary" size="small" link @click.stop="executeCase(item)">
                <el-icon><VideoPlay /></el-icon>
              </el-button>
              <el-button type="danger" size="small" link @click.stop="deleteCase(item)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          
          <el-empty v-if="!loading && cases.length === 0" description="暂无用例" />
        </div>
        
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, prev, pager, next"
          small
          @size-change="loadCases"
          @current-change="loadCases"
        />
      </el-card>
    </div>
    
    <div class="case-editor-panel">
      <el-card class="editor-card">
        <template #header>
          <div class="card-header">
            <span>{{ isNewCase ? '新建用例' : '编辑用例' }}</span>
            <div class="header-actions">
              <el-button size="small" @click="validateYaml" :loading="validating">
                验证
              </el-button>
              <el-button type="primary" size="small" @click="saveCase" :loading="saving">
                保存
              </el-button>
              <el-button v-if="!isNewCase" type="success" size="small" @click="saveAndExecute" :loading="saving">
                保存并执行
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-if="selectedCase || isNewCase" class="editor-content">
          <div class="case-info">
            <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" size="small">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="名称" prop="name">
                    <el-input v-model="form.name" placeholder="用例名称" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="目录">
                    <el-select v-model="form.folder_id" placeholder="选择目录" clearable style="width: 100%">
                      <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="描述">
                <el-input v-model="form.description" placeholder="用例描述" />
              </el-form-item>
              
              <el-row :gutter="16">
                <el-col :span="16">
                  <el-form-item label="标签">
                    <el-select v-model="form.tags" multiple filterable allow-create placeholder="选择标签" style="width: 100%">
                      <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.name" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="模板">
                    <el-switch v-model="form.is_template" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
            
            <el-alert
              v-if="validationResult"
              :title="validationResult.valid ? 'YAML格式正确' : 'YAML格式错误'"
              :type="validationResult.valid ? 'success' : 'error'"
              :description="validationResult.error || undefined"
              show-icon
              :closable="false"
              style="margin-bottom: 12px"
            />
          </div>
          
          <div class="yaml-editor-wrapper">
            <div class="editor-toolbar">
              <span>YAML内容</span>
              <div class="toolbar-actions">
                <el-button size="small" link @click="loadTemplate('case')">Case模板</el-button>
                <el-button size="small" link @click="loadTemplate('workflow')">Workflow模板</el-button>
              </div>
            </div>
            <div class="yaml-editor-container">
              <vue-monaco-editor
                v-model:value="form.yaml_content"
                language="yaml"
                :options="editorOptions"
                @change="onYamlChange"
              />
            </div>
          </div>
        </div>
        
        <el-empty v-else description="请从左侧选择用例或点击新建" />
      </el-card>
    </div>
    
    <el-dialog v-model="showImportDialog" title="导入YAML文件" width="500px">
      <el-form :model="importForm" label-width="100px">
        <el-form-item label="文件路径">
          <el-input v-model="importForm.file_path" placeholder="/app/cases/example.yaml" />
        </el-form-item>
        <el-form-item label="用例名称">
          <el-input v-model="importForm.name" placeholder="留空则使用文件名" />
        </el-form-item>
        <el-form-item label="目录">
          <el-select v-model="importForm.folder_id" placeholder="选择目录" clearable>
            <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="importForm.tags" multiple placeholder="选择标签">
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { caseApi, executionApi, folderApi } from '@/api'
import type { CaseResponse, FolderResponse, TagResponse, CaseValidateResponse } from '@/api/types'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()

const cases = ref<CaseResponse[]>([])
const folders = ref<FolderResponse[]>([])
const tags = ref<TagResponse[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const searchKeyword = ref('')
const filterFolder = ref<number | undefined>(undefined)
const filterTag = ref('')

const selectedCase = ref<CaseResponse | null>(null)
const isNewCase = ref(false)
const hasChanges = ref(false)

const formRef = ref<FormInstance>()
const saving = ref(false)
const validating = ref(false)
const validationResult = ref<CaseValidateResponse | null>(null)

const showImportDialog = ref(false)
const importForm = ref({
  file_path: '',
  name: '',
  folder_id: undefined as number | undefined,
  tags: [] as string[]
})

const form = reactive({
  name: '',
  description: '',
  yaml_content: '',
  folder_id: undefined as number | undefined,
  is_template: false,
  tags: [] as string[]
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  yaml_content: [{ required: true, message: '请输入YAML内容', trigger: 'blur' }]
}

const editorOptions = {
  minimap: { enabled: false },
  fontSize: 13,
  lineNumbers: 'on' as const,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
  wordWrap: 'on' as const
}

const caseTemplate = `name: example_case
description: Example case description
type: network
environment: 1_ssh_remote
fault_type: delay
pod_match:
  name: example-pod
  namespace: default
duration: 60s
loop_count: 1
parameters:
  time: 300ms
  jitter: 100ms
auto_clear: true
`

const workflowTemplate = `workflow:
  id: example_workflow_001
  name: 示例工作流
  description: 工作流描述
  execution_mode: serial
  auto_clear: true
  
  timing:
    start_delay: 5
    node_interval: 10
    task_timeout: 600

  tasks:
    - id: task_1
      name: 任务1
      case:
        name: task1_case
        type: network
        environment: 1_ssh_remote
        fault_type: delay
        pod_match:
          name: example-pod
        duration: 30s
`

watch([() => form.name, () => form.description, () => form.yaml_content, () => form.folder_id, () => form.is_template, () => form.tags], () => {
  hasChanges.value = true
}, { deep: true })

async function checkUnsavedChanges(): Promise<boolean> {
  if (!hasChanges.value) return true
  
  try {
    await ElMessageBox.confirm('当前用例有未保存的更改，是否保存？', '提示', {
      confirmButtonText: '保存',
      cancelButtonText: '不保存',
      distinguishCancelAndClose: true,
      type: 'warning'
    })
    await saveCase()
    return true
  } catch (action: any) {
    if (action === 'cancel') {
      hasChanges.value = false
      return true
    }
    return false
  }
}

async function selectCase(item: CaseResponse) {
  const canProceed = await checkUnsavedChanges()
  if (!canProceed) return
  
  selectedCase.value = item
  isNewCase.value = false
  hasChanges.value = false
  validationResult.value = null
  
  form.name = item.name
  form.description = item.description || ''
  form.yaml_content = item.yaml_content
  form.folder_id = item.folder_id ?? undefined
  form.is_template = item.is_template
  form.tags = item.tags?.map(t => t.name) || []
}

function createNewCase() {
  checkUnsavedChanges().then(canProceed => {
    if (!canProceed) return
    
    selectedCase.value = null
    isNewCase.value = true
    hasChanges.value = false
    validationResult.value = null
    
    form.name = ''
    form.description = ''
    form.yaml_content = caseTemplate
    form.folder_id = undefined
    form.is_template = false
    form.tags = []
  })
}

function loadTemplate(type: string) {
  if (type === 'case') {
    form.yaml_content = caseTemplate
  } else {
    form.yaml_content = workflowTemplate
  }
}

function onYamlChange() {
  validationResult.value = null
}

async function validateYaml() {
  if (!form.yaml_content) {
    ElMessage.warning('请输入YAML内容')
    return
  }
  
  validating.value = true
  try {
    validationResult.value = await caseApi.validate({ yaml_content: form.yaml_content })
  } finally {
    validating.value = false
  }
}

async function saveCase() {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  saving.value = true
  try {
    if (isNewCase.value) {
      const newCase = await caseApi.create(form)
      selectedCase.value = newCase
      isNewCase.value = false
      ElMessage.success('创建成功')
      loadCases()
    } else if (selectedCase.value) {
      await caseApi.update(selectedCase.value.id, form)
      ElMessage.success('保存成功')
      loadCases()
    }
    hasChanges.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveAndExecute() {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  saving.value = true
  try {
    if (selectedCase.value) {
      await caseApi.update(selectedCase.value.id, form)
      const execution = await executionApi.create({ case_id: selectedCase.value.id })
      hasChanges.value = false
      ElMessage.success('保存成功，开始执行')
      router.push(`/executions/${execution.id}`)
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function executeCase(item: CaseResponse) {
  try {
    await ElMessageBox.confirm(`确定要执行用例 "${item.name}" 吗？`, '确认执行')
    const execution = await executionApi.create({ case_id: item.id })
    ElMessage.success('用例已开始执行')
    router.push(`/executions/${execution.id}`)
  } catch (e) {
    // cancelled
  }
}

async function deleteCase(item: CaseResponse) {
  try {
    await ElMessageBox.confirm(`确定要删除用例 "${item.name}" 吗？`, '确认删除', { type: 'warning' })
    await caseApi.delete(item.id)
    ElMessage.success('删除成功')
    if (selectedCase.value?.id === item.id) {
      selectedCase.value = null
    }
    loadCases()
  } catch (e) {
    // cancelled
  }
}

async function loadCases() {
  loading.value = true
  try {
    const response = await caseApi.getList({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined,
      folder_id: filterFolder.value,
      tag: filterTag.value || undefined
    })
    cases.value = response.items
    total.value = response.total
  } finally {
    loading.value = false
  }
}

async function loadFolders() {
  folders.value = await folderApi.getList()
}

async function loadTags() {
  tags.value = await caseApi.getTags()
}

function handleSearch() {
  currentPage.value = 1
  loadCases()
}

function getFolderName(folderId: number): string {
  const folder = folders.value.find(f => f.id === folderId)
  return folder ? folder.name : ''
}

async function handleImport() {
  if (!importForm.value.file_path) {
    ElMessage.warning('请输入文件路径')
    return
  }
  
  try {
    await caseApi.import(importForm.value)
    ElMessage.success('导入成功')
    showImportDialog.value = false
    importForm.value = { file_path: '', name: '', folder_id: undefined, tags: [] }
    loadCases()
    loadFolders()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  }
}

onMounted(() => {
  loadCases()
  loadFolders()
  loadTags()
})

onBeforeUnmount(() => {
  checkUnsavedChanges()
})
</script>

<style scoped lang="scss">
.case-management {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
  
  .case-list-panel {
    width: 350px;
    flex-shrink: 0;
    
    .list-card {
      height: 100%;
      display: flex;
      flex-direction: column;
      
      :deep(.el-card__body) {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        padding: 12px;
      }
    }
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .filter-bar {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 12px;
      
      .el-select {
        width: 100%;
      }
    }
    
    .case-list-container {
      flex: 1;
      overflow-y: auto;
      margin: 0 -12px;
      padding: 0 12px;
    }
    
    .case-item {
      padding: 10px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid transparent;
      margin-bottom: 8px;
      
      &:hover {
        background: #f5f7fa;
      }
      
      &.active {
        background: #ecf5ff;
        border-color: #409eff;
      }
      
      .case-name {
        font-weight: 500;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
      }
      
      .case-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
        font-size: 12px;
        color: #909399;
        
        .folder {
          background: #f4f4f5;
          padding: 2px 6px;
          border-radius: 3px;
        }
      }
      
      .case-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
      
      .case-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 8px;
        opacity: 0;
        transition: opacity 0.2s;
      }
      
      &:hover .case-actions {
        opacity: 1;
      }
    }
    
    .el-pagination {
      margin-top: 12px;
      justify-content: center;
    }
  }
  
  .case-editor-panel {
    flex: 1;
    min-width: 0;
    
    .editor-card {
      height: 100%;
      display: flex;
      flex-direction: column;
      
      :deep(.el-card__body) {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        padding: 12px;
      }
    }
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        gap: 8px;
      }
    }
    
    .editor-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .case-info {
      flex-shrink: 0;
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid #ebeef5;
    }
    
    .yaml-editor-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
      
      .editor-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        font-weight: 500;
        
        .toolbar-actions {
          display: flex;
          gap: 8px;
        }
      }
      
      .yaml-editor-container {
        flex: 1;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        overflow: hidden;
        min-height: 300px;
      }
    }
  }
}
</style>
