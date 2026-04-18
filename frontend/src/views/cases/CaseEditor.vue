<template>
  <div class="case-editor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑用例' : '创建用例' }}</span>
          <div class="header-actions">
            <el-button @click="validateYaml" :loading="validating">
              验证YAML
            </el-button>
            <el-button type="primary" @click="saveCase" :loading="saving">
              保存
            </el-button>
            <el-button v-if="isEdit" type="success" @click="saveAndExecute" :loading="saving">
              保存并执行
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用例名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入用例名称" />
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
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="用例描述" />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple filterable allow-create placeholder="选择或创建标签">
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.name" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模板">
          <el-switch v-model="form.is_template" />
          <span style="margin-left: 8px; color: #909399">设为模板后可快速创建新用例</span>
        </el-form-item>
        
        <el-form-item label="YAML内容" prop="yaml_content">
          <div class="yaml-editor-container">
            <vue-monaco-editor
              v-model:value="form.yaml_content"
              language="yaml"
              :options="editorOptions"
              @change="onYamlChange"
            />
          </div>
        </el-form-item>
        
        <el-form-item v-if="validationResult">
          <el-alert
            :title="validationResult.valid ? 'YAML格式正确' : 'YAML格式错误'"
            :type="validationResult.valid ? 'success' : 'error'"
            :description="validationResult.error || undefined"
            show-icon
          />
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <span>YAML模板</span>
      </template>
      <div class="templates">
        <el-button @click="loadTemplate('case')">Case模板</el-button>
        <el-button @click="loadTemplate('workflow')">Workflow模板</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { caseApi, executionApi, folderApi } from '@/api'
import type { FolderResponse, TagResponse, CaseValidateResponse } from '@/api/types'
import type { FormInstance, FormRules } from 'element-plus'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const caseId = computed(() => Number(route.params.id))

const formRef = ref<FormInstance>()
const saving = ref(false)
const validating = ref(false)
const validationResult = ref<CaseValidateResponse | null>(null)
const tags = ref<TagResponse[]>([])
const folders = ref<FolderResponse[]>([])

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
  fontSize: 14,
  lineNumbers: 'on' as const,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2
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
    if (isEdit.value) {
      await caseApi.update(caseId.value, form)
    } else {
      await caseApi.create(form)
    }
    ElMessage.success('保存成功')
    router.push('/cases')
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
    await caseApi.update(caseId.value, form)
    const execution = await executionApi.create({ case_id: caseId.value })
    ElMessage.success('保存成功，开始执行')
    router.push(`/executions/${execution.id}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function loadCase() {
  if (!isEdit.value) return
  
  try {
    const caseData = await caseApi.get(caseId.value)
    form.name = caseData.name
    form.description = caseData.description || ''
    form.yaml_content = caseData.yaml_content
    form.folder_id = caseData.folder_id ?? undefined
    form.is_template = caseData.is_template
    form.tags = caseData.tags.map(t => t.name)
  } catch (e) {
    ElMessage.error('加载用例失败')
    router.push('/cases')
  }
}

async function loadTags() {
  tags.value = await caseApi.getTags()
}

async function loadFolders() {
  folders.value = await folderApi.getList()
}

onMounted(() => {
  loadCase()
  loadTags()
  loadFolders()
})
</script>

<style scoped lang="scss">
.case-editor {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .yaml-editor-container {
    width: 100%;
    height: 500px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .templates {
    display: flex;
    gap: 12px;
  }
}
</style>
