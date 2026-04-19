<template>
  <div class="workflow-editor">
    <div class="sidebar">
      <el-card class="sidebar-card">
        <template #header>
          <div class="sidebar-header">
            <span>用例管理</span>
            <el-dropdown trigger="click" @command="handleNewCommand">
              <el-button type="primary" size="small">
                <el-icon><Plus /></el-icon>
                新建
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="folder">
                    <el-icon><FolderAdd /></el-icon>
                    新建目录
                  </el-dropdown-item>
                  <el-dropdown-item command="case">
                    <el-icon><Document /></el-icon>
                    新建用例
                  </el-dropdown-item>
                  <el-dropdown-item command="workflow">
                    <el-icon><Share /></el-icon>
                    新建工作流
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        
        <div class="sidebar-search">
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
        </div>
        
        <div class="tree-container" v-loading="loading">
          <el-tree
            :data="treeData"
            :props="treeProps"
            node-key="id"
            :expand-on-click-node="false"
            :highlight-current="true"
            :default-expand-all="true"
            :allow-drop="allowDrop"
            :allow-drag="allowDrag"
            draggable
            @node-click="handleNodeClick"
            @node-contextmenu="handleContextMenu"
            @node-drop="handleDrop"
            @node-drag-start="handleNodeDragStart"
          >
            <template #default="{ node, data }">
              <div class="tree-node" :class="{ 'is-folder': data.type === 'folder' }">
                <el-icon class="node-icon">
                  <Folder v-if="data.type === 'folder'" />
                  <Document v-else-if="data.case_type === 'case'" />
                  <Share v-else />
                </el-icon>
                <span class="node-label">{{ node.label }}</span>
                <span v-if="data.type === 'folder'" class="node-count">{{ data.case_count || 0 }}</span>
              </div>
            </template>
          </el-tree>
          
          <el-empty v-if="!loading && treeData.length === 0" description="暂无内容" :image-size="60" />
        </div>
        
        <div class="sidebar-tips">
          <el-text size="small" type="info">拖拽用例到右侧画布添加节点</el-text>
        </div>
      </el-card>
    </div>
    
    <div class="canvas-container">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="workflowName"
            placeholder="工作流名称"
            style="width: 200px"
            size="small"
          />
          <el-input
            v-model="workflowDescription"
            placeholder="工作流描述"
            style="width: 300px; margin-left: 12px"
            size="small"
          />
        </div>
        <div class="toolbar-right">
          <el-button-group>
            <el-button size="small" @click="undo" :disabled="!canUndo">
              <el-icon><Back /></el-icon>
              撤销
            </el-button>
            <el-button size="small" @click="redo" :disabled="!canRedo">
              <el-icon><Right /></el-icon>
              重做
            </el-button>
          </el-button-group>
          <el-button size="small" @click="validateWorkflow">
            <el-icon><Check /></el-icon>
            验证
          </el-button>
          <el-button type="primary" size="small" @click="saveWorkflow" :loading="saving">
            <el-icon><DocumentChecked /></el-icon>
            保存
          </el-button>
          <el-button type="success" size="small" @click="executeWorkflow" :loading="executing">
            <el-icon><VideoPlay /></el-icon>
            执行
          </el-button>
        </div>
      </div>
      
      <div class="flow-container" @drop="onDrop" @dragover="onDragOver">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :default-edge-options="defaultEdgeOptions"
          :connection-line-style="connectionLineStyle"
          :snap-to-grid="true"
          :snap-grid="[15, 15]"
          fit-view-on-init
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
          @connect="onConnect"
        >
          <Background :gap="20" :size="1" />
          <Controls />
          <MiniMap />
          
          <template #node-start>
            <StartNode />
          </template>
          
          <template #node-end>
            <EndNode />
          </template>
          
          <template #node-case="nodeProps">
            <CaseNode
              :data="nodeProps.data"
              :id="nodeProps.id"
              :selected="nodeProps.selected"
              @edit="editNode"
              @delete="deleteNode"
              @copy="copyNode"
            />
          </template>
          
          <template #node-workflow="nodeProps">
            <WorkflowNode
              :data="nodeProps.data"
              :id="nodeProps.id"
              :selected="nodeProps.selected"
              @edit="editNode"
              @delete="deleteNode"
              @copy="copyNode"
            />
          </template>
        </VueFlow>
      </div>
    </div>
    
    <el-dialog
      v-model="showNodeDialog"
      :title="nodeDialogTitle"
      width="800px"
      destroy-on-close
    >
      <el-form :model="nodeForm" label-width="100px" size="small">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="节点名称">
              <el-input v-model="nodeForm.label" placeholder="节点名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="失败处理">
              <el-select v-model="nodeForm.onFailure" style="width: 100%">
                <el-option label="停止后续执行" value="stop" />
                <el-option label="继续执行" value="continue" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="超时时间">
          <el-input-number v-model="nodeForm.timeout" :min="0" :max="3600" />
          <span style="margin-left: 8px; color: #909399">秒（0表示不限制）</span>
        </el-form-item>
        
        <el-form-item label="YAML内容">
          <div class="yaml-editor-dialog">
            <vue-monaco-editor
              v-model:value="nodeForm.yaml_content"
              language="yaml"
              :options="editorOptions"
            />
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showNodeDialog = false">取消</el-button>
        <el-button type="primary" @click="saveNode">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showEdgeDialog"
      title="连接配置"
      width="500px"
    >
      <el-form :model="edgeForm" label-width="100px" size="small">
        <el-form-item label="条件类型">
          <el-radio-group v-model="edgeForm.conditionType">
            <el-radio value="always">总是执行</el-radio>
            <el-radio value="onSuccess">成功时执行</el-radio>
            <el-radio value="onFailure">失败时执行</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item v-if="edgeForm.conditionType !== 'always'" label="条件表达式">
          <el-input
            v-model="edgeForm.condition"
            type="textarea"
            :rows="3"
            placeholder="例如: result.status == 'success'"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEdgeDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdge">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showFolderDialog"
      :title="folderDialogTitle"
      width="400px"
    >
      <el-form :model="folderForm" label-width="80px" size="small">
        <el-form-item label="目录名称">
          <el-input v-model="folderForm.name" placeholder="请输入目录名称" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showFolderDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFolder">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showRenameDialog"
      title="重命名"
      width="400px"
    >
      <el-form :model="renameForm" label-width="80px" size="small">
        <el-form-item label="名称">
          <el-input v-model="renameForm.name" placeholder="请输入名称" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showRenameDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRename">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showCaseDialog"
      :title="caseDialogTitle"
      width="800px"
      destroy-on-close
    >
      <el-form :model="caseForm" label-width="100px" size="small">
        <el-form-item label="名称">
          <el-input v-model="caseForm.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="caseForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="caseForm.case_type">
            <el-radio value="case">用例</el-radio>
            <el-radio value="workflow">工作流</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="YAML内容">
          <div class="yaml-editor-dialog">
            <vue-monaco-editor
              v-model:value="caseForm.yaml_content"
              language="yaml"
              :options="editorOptions"
            />
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCaseDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCase" :loading="savingCase">确定</el-button>
      </template>
    </el-dialog>
    
    <ContextMenu ref="contextMenuRef">
      <template v-if="contextMenuData.type === 'folder'">
        <ContextMenuItem @click="createSubFolder">新建子目录</ContextMenuItem>
        <ContextMenuItem @click="renameItem">重命名</ContextMenuItem>
        <ContextMenuItem :divided="true" @click="deleteFolder">删除</ContextMenuItem>
      </template>
      <template v-else>
        <ContextMenuItem @click="editCaseItem">编辑</ContextMenuItem>
        <ContextMenuItem @click="copyCaseItem">复制</ContextMenuItem>
        <ContextMenuItem @click="renameItem">重命名</ContextMenuItem>
        <ContextMenuItem :divided="true" @click="deleteCaseItem">删除</ContextMenuItem>
      </template>
    </ContextMenu>
    
    <el-drawer
      v-model="showCaseDetail"
      :title="selectedCase?.name || '用例详情'"
      direction="rtl"
      size="50%"
    >
      <template v-if="selectedCase">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ selectedCase.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="selectedCase.case_type === 'workflow' ? 'success' : 'info'">
              {{ selectedCase.case_type === 'workflow' ? '工作流' : '用例' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedCase.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedCase.created_at }}</el-descriptions-item>
          <el-descriptions-item label="标签">
            <el-tag v-for="tag in selectedCase.tags" :key="tag.id" size="small" style="margin-right: 4px">
              {{ tag.name }}
            </el-tag>
            <span v-if="!selectedCase.tags?.length">无</span>
          </el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-top: 16px">
          <div style="margin-bottom: 8px; font-weight: bold">YAML 内容</div>
          <div class="yaml-editor-detail">
            <vue-monaco-editor
              :key="selectedCase?.id"
              v-model:value="selectedCase.yaml_content"
              language="yaml"
              :options="{ ...editorOptions, readOnly: true }"
            />
          </div>
        </div>
        
        <div style="margin-top: 16px">
          <el-button type="primary" @click="editSelectedCase">编辑</el-button>
          <el-button type="success" @click="executeSelectedCase" :loading="executing">执行</el-button>
          <el-button @click="copySelectedCase">复制</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElTree } from 'element-plus'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import ContextMenu from '@/components/ContextMenu.vue'
import ContextMenuItem from '@/components/ContextMenuItem.vue'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import type { Node, Edge, Connection, NodeMouseEvent, EdgeMouseEvent } from '@vue-flow/core'
import type { CaseResponse, FolderResponse } from '@/api/types'
import { caseApi, folderApi, executionApi } from '@/api'

import StartNode from './nodes/StartNode.vue'
import EndNode from './nodes/EndNode.vue'
import CaseNode from './nodes/CaseNode.vue'
import WorkflowNode from './nodes/WorkflowNode.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

interface TreeNode {
  id: string | number
  label: string
  type: 'folder' | 'case'
  case_type?: string
  case_count?: number
  parent_id?: number | null
  children?: TreeNode[]
  data?: CaseResponse | FolderResponse
}

const router = useRouter()
const contextMenuRef = ref()

const { addNodes, addEdges, removeNodes } = useVueFlow()

const folders = ref<FolderResponse[]>([])
const cases = ref<CaseResponse[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const selectedFolderId = ref<number | null>(null)
const selectedCase = ref<CaseResponse | null>(null)
const showCaseDetail = ref(false)

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])

const workflowName = ref('')
const workflowDescription = ref('')
const saving = ref(false)
const executing = ref(false)

const history = ref<{ nodes: Node[]; edges: Edge[] }[]>([])
const historyIndex = ref(-1)
const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

const showNodeDialog = ref(false)
const nodeDialogTitle = ref('')
const currentNodeId = ref('')
const nodeForm = reactive({
  label: '',
  yaml_content: '',
  onFailure: 'stop',
  timeout: 0
})

const showEdgeDialog = ref(false)
const currentEdgeId = ref('')
const edgeForm = reactive({
  conditionType: 'always',
  condition: ''
})

const showFolderDialog = ref(false)
const folderDialogTitle = ref('')
const currentFolderId = ref<number | null>(null)
const folderForm = reactive({
  name: '',
  parent_id: undefined as number | undefined
})

const showRenameDialog = ref(false)
const renameForm = reactive({
  name: ''
})

const showCaseDialog = ref(false)
const caseDialogTitle = ref('')
const currentCaseId = ref<number | null>(null)
const savingCase = ref(false)
const caseForm = reactive({
  name: '',
  description: '',
  yaml_content: '',
  case_type: 'case' as 'case' | 'workflow',
  folder_id: undefined as number | undefined
})

const contextMenuData = reactive<{
  type: 'folder' | 'case'
  id: number
  data: FolderResponse | CaseResponse | null
}>({
  type: 'folder',
  id: 0,
  data: null
})

const defaultEdgeOptions = {
  type: 'smoothstep',
  animated: true,
  style: { stroke: '#409eff', strokeWidth: 2 }
}

const connectionLineStyle = { stroke: '#409eff', strokeWidth: 2 }

const editorOptions = {
  minimap: { enabled: false },
  fontSize: 13,
  lineNumbers: 'on' as const,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
  wordWrap: 'on' as const
}

const treeProps = {
  children: 'children',
  label: 'label'
}

function buildFolderNode(folder: FolderResponse): TreeNode {
  const node: TreeNode = {
    id: `folder_${folder.id}`,
    label: folder.name,
    type: 'folder' as const,
    case_count: folder.case_count,
    parent_id: folder.parent_id,
    children: [],
    data: folder
  }
  
  if (folder.children && folder.children.length > 0) {
    node.children = folder.children.map(child => buildFolderNode(child))
  }
  
  return node
}

const treeData = computed<TreeNode[]>(() => {
  console.log('Computing treeData, cases:', cases.value)
  const folderNodes: TreeNode[] = folders.value.map(f => buildFolderNode(f))
  
  const caseNodes: TreeNode[] = cases.value.map(c => {
    console.log('Creating caseNode for:', c.id, c.name, 'data:', c)
    return {
      id: `case_${c.id}`,
      label: c.name,
      type: 'case' as const,
      case_type: c.case_type || 'case',
      parent_id: c.folder_id,
      data: c
    }
  })
  
  const folderMap = new Map<string, TreeNode>()
  function collectFolders(nodes: TreeNode[]) {
    nodes.forEach(n => {
      folderMap.set(String(n.id), n)
      if (n.children && n.children.length > 0) {
        collectFolders(n.children)
      }
    })
  }
  collectFolders(folderNodes)
  
  caseNodes.forEach(c => {
    if (c.parent_id) {
      const folder = folderMap.get(`folder_${c.parent_id}`)
      if (folder) {
        folder.children = folder.children || []
        folder.children.push(c)
      }
    } else {
      folderNodes.push(c)
    }
  })
  
  console.log('Final treeData:', folderNodes)
  return folderNodes
})

function initWorkflow() {
  nodes.value = [
    {
      id: 'start',
      type: 'start',
      position: { x: 250, y: 50 },
      data: { label: '开始' }
    },
    {
      id: 'end',
      type: 'end',
      position: { x: 250, y: 500 },
      data: { label: '结束' }
    }
  ]
  edges.value = []
  saveToHistory()
}

function saveToHistory() {
  const state = {
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value))
  }
  
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  
  history.value.push(state)
  historyIndex.value = history.value.length - 1
}

function undo() {
  if (historyIndex.value > 0) {
    historyIndex.value--
    const state = history.value[historyIndex.value]
    nodes.value = JSON.parse(JSON.stringify(state.nodes))
    edges.value = JSON.parse(JSON.stringify(state.edges))
  }
}

function redo() {
  if (historyIndex.value < history.value.length - 1) {
    historyIndex.value++
    const state = history.value[historyIndex.value]
    nodes.value = JSON.parse(JSON.stringify(state.nodes))
    edges.value = JSON.parse(JSON.stringify(state.edges))
  }
}

async function loadData() {
  loading.value = true
  try {
    const [foldersRes, casesRes] = await Promise.all([
      folderApi.getList(),
      caseApi.getList({ page: 1, page_size: 1000, keyword: searchKeyword.value || undefined })
    ])
    folders.value = foldersRes
    cases.value = casesRes.items
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadData()
}

function handleNewCommand(command: string) {
  if (command === 'folder') {
    folderDialogTitle.value = '新建目录'
    folderForm.name = ''
    folderForm.parent_id = selectedFolderId.value || undefined
    currentFolderId.value = null
    showFolderDialog.value = true
  } else if (command === 'case' || command === 'workflow') {
    caseDialogTitle.value = command === 'case' ? '新建用例' : '新建工作流'
    caseForm.name = ''
    caseForm.description = ''
    caseForm.yaml_content = ''
    caseForm.case_type = command
    caseForm.folder_id = selectedFolderId.value || undefined
    currentCaseId.value = null
    showCaseDialog.value = true
  }
}

function handleNodeClick(data: TreeNode, _node: any) {
  console.log('handleNodeClick data:', data)
  if (data.type === 'folder') {
    selectedFolderId.value = Number(data.id.toString().replace('folder_', ''))
  } else if (data.type === 'case' && data.data) {
    console.log('Setting selectedCase:', data.data)
    selectedCase.value = data.data as CaseResponse
    showCaseDetail.value = true
  }
}

function editSelectedCase() {
  console.log('editSelectedCase called, selectedCase:', selectedCase.value)
  if (!selectedCase.value) return
  const caseId = selectedCase.value.id
  console.log('caseId:', caseId)
  if (!caseId) {
    ElMessage.error('用例ID无效')
    return
  }
  caseDialogTitle.value = '编辑用例'
  caseForm.name = selectedCase.value.name
  caseForm.description = selectedCase.value.description || ''
  caseForm.yaml_content = selectedCase.value.yaml_content
  caseForm.case_type = (selectedCase.value.case_type as 'case' | 'workflow') || 'case'
  caseForm.folder_id = selectedCase.value.folder_id ?? undefined
  currentCaseId.value = caseId
  console.log('currentCaseId set to:', currentCaseId.value)
  showCaseDetail.value = false
  showCaseDialog.value = true
}

async function executeSelectedCase() {
  if (!selectedCase.value) return
  try {
    executing.value = true
    const result = await executionApi.create({
      case_id: selectedCase.value.id
    })
    ElMessage.success('执行已启动')
    showCaseDetail.value = false
    router.push(`/executions/${result.id}`)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '执行失败')
  } finally {
    executing.value = false
  }
}

async function copySelectedCase() {
  if (!selectedCase.value) return
  try {
    await caseApi.copy(selectedCase.value.id, { name: `${selectedCase.value.name} - 副本` })
    ElMessage.success('复制成功')
    showCaseDetail.value = false
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '复制失败')
  }
}

function handleContextMenu(evt: Event, data: TreeNode, _node: any, _nodeInstance: any) {
  const event = evt as MouseEvent
  event.preventDefault()
  contextMenuData.type = data.type
  contextMenuData.id = Number(data.id.toString().replace('folder_', '').replace('case_', ''))
  contextMenuData.data = data.data || null
  contextMenuRef.value?.show(event.clientX, event.clientY)
}

function createSubFolder() {
  folderDialogTitle.value = '新建子目录'
  folderForm.name = ''
  folderForm.parent_id = contextMenuData.id
  currentFolderId.value = null
  showFolderDialog.value = true
}

async function saveFolder() {
  if (!folderForm.name.trim()) {
    ElMessage.warning('请输入目录名称')
    return
  }
  
  try {
    if (currentFolderId.value) {
      await folderApi.update(currentFolderId.value, { name: folderForm.name })
      ElMessage.success('更新成功')
    } else {
      await folderApi.create({ name: folderForm.name, parent_id: folderForm.parent_id || undefined })
      ElMessage.success('创建成功')
    }
    showFolderDialog.value = false
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

function renameItem() {
  if (contextMenuData.data) {
    renameForm.name = contextMenuData.data.name
    showRenameDialog.value = true
  }
}

async function saveRename() {
  if (!renameForm.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  
  try {
    if (contextMenuData.type === 'folder') {
      await folderApi.update(contextMenuData.id, { name: renameForm.name })
    } else {
      await caseApi.rename(contextMenuData.id, { name: renameForm.name })
    }
    ElMessage.success('重命名成功')
    showRenameDialog.value = false
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

async function deleteFolder() {
  try {
    await ElMessageBox.confirm('确定要删除此目录吗？目录内的用例也会被删除。', '确认删除', { type: 'warning' })
    await folderApi.delete(contextMenuData.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: unknown) {
    if (e !== 'cancel') {
      const err = e as { response?: { data?: { detail?: string } } }
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

function editCaseItem() {
  if (contextMenuData.data) {
    const caseData = contextMenuData.data as CaseResponse
    caseDialogTitle.value = '编辑用例'
    caseForm.name = caseData.name
    caseForm.description = caseData.description || ''
    caseForm.yaml_content = caseData.yaml_content
    caseForm.case_type = (caseData.case_type as 'case' | 'workflow') || 'case'
    caseForm.folder_id = caseData.folder_id != null ? caseData.folder_id : undefined
    currentCaseId.value = contextMenuData.id
    showCaseDialog.value = true
  }
}

async function copyCaseItem() {
  try {
    await caseApi.copy(contextMenuData.id)
    ElMessage.success('复制成功')
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '复制失败')
  }
}

async function deleteCaseItem() {
  try {
    await ElMessageBox.confirm('确定要删除此用例吗？', '确认删除', { type: 'warning' })
    await caseApi.delete(contextMenuData.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: unknown) {
    if (e !== 'cancel') {
      const err = e as { response?: { data?: { detail?: string } } }
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

async function saveCase() {
  console.log('saveCase called, currentCaseId:', currentCaseId.value)
  if (!caseForm.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  
  savingCase.value = true
  try {
    if (currentCaseId.value) {
      console.log('Updating case:', currentCaseId.value)
      await caseApi.update(currentCaseId.value, {
        name: caseForm.name,
        description: caseForm.description,
        yaml_content: caseForm.yaml_content,
        case_type: caseForm.case_type,
        folder_id: caseForm.folder_id || undefined
      })
      ElMessage.success('更新成功')
    } else {
      await caseApi.create({
        name: caseForm.name,
        description: caseForm.description,
        yaml_content: caseForm.yaml_content,
        case_type: caseForm.case_type,
        folder_id: caseForm.folder_id || undefined
      })
      ElMessage.success('创建成功')
    }
    showCaseDialog.value = false
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    savingCase.value = false
  }
}

function allowDrag(_draggingNode: any) {
  return true
}

function allowDrop(draggingNode: any, dropNode: any, type: string) {
  if (draggingNode.data.type === 'folder') {
    return type !== 'inner' || dropNode.data.type === 'folder'
  }
  return true
}

async function handleDrop(draggingNode: any, dropNode: any, dropType: string) {
  const dragId = Number(draggingNode.data.id.toString().replace('folder_', '').replace('case_', ''))
  const dropId = Number(dropNode.data.id.toString().replace('folder_', '').replace('case_', ''))
  
  try {
    if (draggingNode.data.type === 'folder') {
      let newParentId: number | undefined = undefined
      if (dropType === 'inner') {
        newParentId = dropId
      } else if (dropNode.data.parent_id) {
        newParentId = dropNode.data.parent_id
      }
      await folderApi.update(dragId, { parent_id: newParentId })
    } else {
      let newFolderId: number | undefined = undefined
      if (dropType === 'inner' && dropNode.data.type === 'folder') {
        newFolderId = dropId
      } else if (dropNode.data.type === 'case' && dropNode.data.parent_id) {
        newFolderId = Number(dropNode.data.parent_id)
      }
      await caseApi.move(dragId, { folder_id: newFolderId })
    }
    ElMessage.success('移动成功')
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '移动失败')
  }
}

function handleNodeDragStart(node: any, ev: DragEvent) {
  const data = node.data as TreeNode
  if (data.type !== 'case' || !data.data) return
  
  const caseData = data.data as CaseResponse
  if (ev.dataTransfer) {
    ev.dataTransfer.setData('application/vueflow', JSON.stringify({
      type: caseData.case_type === 'workflow' ? 'workflow' : 'case',
      data: {
        caseId: caseData.id,
        label: caseData.name,
        yaml_content: caseData.yaml_content,
        onFailure: 'stop',
        timeout: 0
      }
    }))
    ev.dataTransfer.effectAllowed = 'move'
  }
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

function onDrop(event: DragEvent) {
  const data = event.dataTransfer?.getData('application/vueflow')
  if (!data) return
  
  const { type, data: nodeData } = JSON.parse(data)
  
  const bounds = (event.target as HTMLElement).closest('.flow-container')?.getBoundingClientRect()
  if (!bounds) return
  
  const position = {
    x: event.clientX - bounds.left - 100,
    y: event.clientY - bounds.top - 30
  }
  
  const newNode = {
    id: `node_${Date.now()}`,
    type,
    position,
    data: nodeData
  }
  
  addNodes([newNode])
  saveToHistory()
}

function onConnect(connection: Connection) {
  const newEdge = {
    id: `edge_${Date.now()}`,
    source: connection.source,
    target: connection.target,
    sourceHandle: connection.sourceHandle,
    targetHandle: connection.targetHandle,
    type: 'smoothstep',
    animated: true,
    data: { conditionType: 'always' }
  }
  addEdges([newEdge])
  saveToHistory()
}

function onNodeClick(event: NodeMouseEvent) {
  const node = event.node
  if (node.type === 'start' || node.type === 'end') return
  
  currentNodeId.value = node.id
  const nodeData = node.data as Record<string, unknown>
  nodeDialogTitle.value = `编辑节点 - ${(nodeData.label as string) || ''}`
  nodeForm.label = (nodeData.label as string) || ''
  nodeForm.yaml_content = (nodeData.yaml_content as string) || ''
  nodeForm.onFailure = (nodeData.onFailure as string) || 'stop'
  nodeForm.timeout = (nodeData.timeout as number) || 0
  showNodeDialog.value = true
}

function onEdgeClick(event: EdgeMouseEvent) {
  const edge = event.edge
  currentEdgeId.value = edge.id
  edgeForm.conditionType = edge.data?.conditionType || 'always'
  edgeForm.condition = edge.data?.condition || ''
  showEdgeDialog.value = true
}

function editNode(nodeId: string) {
  const node = nodes.value.find((n: { id: string }) => n.id === nodeId)
  if (node) {
    currentNodeId.value = node.id
    const nodeData = node.data as Record<string, unknown>
    nodeDialogTitle.value = `编辑节点 - ${(nodeData.label as string) || ''}`
    nodeForm.label = (nodeData.label as string) || ''
    nodeForm.yaml_content = (nodeData.yaml_content as string) || ''
    nodeForm.onFailure = (nodeData.onFailure as string) || 'stop'
    nodeForm.timeout = (nodeData.timeout as number) || 0
    showNodeDialog.value = true
  }
}

function saveNode() {
  const node = nodes.value.find((n: { id: string }) => n.id === currentNodeId.value)
  if (node) {
    node.data = {
      ...node.data,
      label: nodeForm.label,
      yaml_content: nodeForm.yaml_content,
      onFailure: nodeForm.onFailure,
      timeout: nodeForm.timeout
    }
    saveToHistory()
  }
  showNodeDialog.value = false
}

function deleteNode(nodeId: string) {
  ElMessageBox.confirm('确定要删除此节点吗？', '确认删除', { type: 'warning' })
    .then(() => {
      removeNodes([nodeId])
      saveToHistory()
    })
    .catch(() => {})
}

function copyNode(nodeId: string) {
  const node = nodes.value.find((n: { id: string }) => n.id === nodeId)
  if (node) {
    const newNode = {
      id: `node_${Date.now()}`,
      type: node.type,
      position: { x: node.position.x + 50, y: node.position.y + 50 },
      data: { ...node.data }
    }
    addNodes([newNode])
    saveToHistory()
  }
}

function saveEdge() {
  const edge = edges.value.find((e: any) => e.id === currentEdgeId.value)
  if (edge) {
    edge.data = {
      conditionType: edgeForm.conditionType,
      condition: edgeForm.condition
    }
    
    const colorMap: Record<string, string> = {
      always: '#409eff',
      onSuccess: '#67c23a',
      onFailure: '#f56c6c'
    }
    edge.style = { stroke: colorMap[edgeForm.conditionType], strokeWidth: 2 }
    
    saveToHistory()
  }
  showEdgeDialog.value = false
}

function validateWorkflow(): boolean {
  const hasStart = nodes.value.some((n: any) => n.type === 'start')
  const hasEnd = nodes.value.some((n: any) => n.type === 'end')
  
  if (!hasStart || !hasEnd) {
    ElMessage.error('工作流必须包含开始和结束节点')
    return false
  }
  
  const taskNodes = nodes.value.filter((n: any) => n.type === 'case' || n.type === 'workflow')
  if (taskNodes.length === 0) {
    ElMessage.error('工作流至少需要一个任务节点')
    return false
  }
  
  const connectedNodeIds = new Set<string>()
  edges.value.forEach((e: any) => {
    connectedNodeIds.add(e.source)
    connectedNodeIds.add(e.target)
  })
  
  const isolatedNodes = taskNodes.filter((n: any) => !connectedNodeIds.has(n.id))
  if (isolatedNodes.length > 0) {
    ElMessage.error('存在未连接的节点')
    return false
  }
  
  for (const node of taskNodes) {
    const nodeData = node.data as Record<string, unknown>
    if (!nodeData.yaml_content) {
      ElMessage.error(`节点 "${nodeData.label}" 缺少 YAML 内容`)
      return false
    }
  }
  
  ElMessage.success('工作流验证通过')
  return true
}

async function saveWorkflow() {
  if (!validateWorkflow()) return
  
  try {
    await ElMessageBox.confirm('确定要保存此工作流吗？', '确认保存')
  } catch {
    return
  }
  
  saving.value = true
  try {
    const yamlContent = generateWorkflowYaml()
    
    const workflowData = {
      name: workflowName.value || '未命名工作流',
      description: workflowDescription.value,
      yaml_content: yamlContent,
      case_type: 'workflow',
      folder_id: selectedFolderId.value || undefined
    }
    
    await caseApi.create(workflowData)
    ElMessage.success('保存成功')
    loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function generateWorkflowYaml(): string {
  const nodeOrder = getNodeOrder()
  
  const tasks: Record<string, unknown>[] = []
  
  nodeOrder.forEach((nodeId: string, index: number) => {
    const node = nodes.value.find((n: any) => n.id === nodeId)
    if (!node || node.type === 'start' || node.type === 'end') return
    
    const nodeData = node.data as Record<string, unknown>
    const task: Record<string, unknown> = {
      id: `task_${index + 1}`,
      name: nodeData.label,
      case: parseYamlToCase(nodeData.yaml_content as string)
    }
    
    if (nodeData.onFailure === 'stop') {
      task.stop_on_failure = true
    }
    
    if (nodeData.timeout && (nodeData.timeout as number) > 0) {
      task.timeout = nodeData.timeout
    }
    
    tasks.push(task)
  })
  
  const workflow = {
    workflow: {
      id: `workflow_${Date.now()}`,
      name: workflowName.value || '未命名工作流',
      description: workflowDescription.value,
      execution_mode: 'serial',
      auto_clear: true,
      timing: {
        start_delay: 0,
        node_interval: 0,
        task_timeout: 3600
      },
      tasks
    }
  }
  
  return yamlDump(workflow)
}

function getNodeOrder(): string[] {
  const order: string[] = []
  const visited = new Set<string>()
  
  function dfs(nodeId: string) {
    if (visited.has(nodeId)) return
    visited.add(nodeId)
    order.push(nodeId)
    
    const outgoingEdges = edges.value.filter((e: any) => e.source === nodeId)
    outgoingEdges.forEach((edge: any) => {
      dfs(edge.target)
    })
  }
  
  const startNode = nodes.value.find((n: any) => n.type === 'start')
  if (startNode) {
    dfs(startNode.id)
  }
  
  return order
}

function parseYamlToCase(yamlContent: string): Record<string, unknown> {
  try {
    const lines = yamlContent.split('\n')
    const result: Record<string, unknown> = {}
    
    lines.forEach(line => {
      const match = line.match(/^(\w+):\s*(.*)$/)
      if (match) {
        const [, key, value] = match
        if (value && !value.includes('\n')) {
          result[key] = value.trim()
        }
      }
    })
    
    return result
  } catch {
    return { raw: yamlContent }
  }
}

function yamlDump(obj: Record<string, unknown>): string {
  let result = ''
  
  function dump(value: unknown, indent: number = 0): string {
    const spaces = '  '.repeat(indent)
    
    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value)) {
        let str = '\n'
        value.forEach(item => {
          if (typeof item === 'object' && item !== null) {
            str += `${spaces}-\n${dump(item, indent + 1).slice(0, -1)}\n`
          } else {
            str += `${spaces}- ${item}\n`
          }
        })
        return str
      } else {
        let str = '\n'
        Object.entries(value as Record<string, unknown>).forEach(([k, v]) => {
          if (typeof v === 'object' && v !== null) {
            str += `${spaces}${k}:${dump(v, indent + 1)}`
          } else {
            str += `${spaces}${k}: ${v}\n`
          }
        })
        return str
      }
    }
    
    return `${value}\n`
  }
  
  Object.entries(obj).forEach(([key, value]) => {
    if (typeof value === 'object' && value !== null) {
      result += `${key}:${dump(value, 1)}`
    } else {
      result += `${key}: ${value}\n`
    }
  })
  
  return result
}

async function executeWorkflow() {
  if (!validateWorkflow()) return
  
  try {
    await ElMessageBox.confirm('确定要执行此工作流吗？', '确认执行')
    
    const yamlContent = generateWorkflowYaml()
    
    const workflowData = {
      name: workflowName.value || '未命名工作流',
      description: workflowDescription.value,
      yaml_content: yamlContent,
      case_type: 'workflow',
      folder_id: selectedFolderId.value || undefined
    }
    
    const savedCase = await caseApi.create(workflowData)
    const execution = await executionApi.create({ case_id: savedCase.id })
    
    ElMessage.success('工作流已开始执行')
    router.push(`/executions/${execution.id}`)
  } catch (e: unknown) {
    if (e !== 'cancel') {
      const err = e as { response?: { data?: { detail?: string } } }
      ElMessage.error(err.response?.data?.detail || '执行失败')
    }
  }
}

onMounted(() => {
  loadData()
  initWorkflow()
})
</script>

<style scoped lang="scss">
.workflow-editor {
  display: flex;
  height: calc(100vh - 120px);
  gap: 12px;
  
  .sidebar {
    width: 300px;
    flex-shrink: 0;
    
    .sidebar-card {
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
    
    .sidebar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .sidebar-search {
      margin-bottom: 12px;
    }
    
    .tree-container {
      flex: 1;
      overflow-y: auto;
    }
    
    .tree-node {
      display: flex;
      align-items: center;
      width: 100%;
      padding: 4px 0;
      
      .node-icon {
        margin-right: 8px;
        font-size: 16px;
        color: #909399;
      }
      
      .node-label {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .node-count {
        font-size: 12px;
        color: #909399;
        margin-left: 8px;
      }
      
      &.is-folder .node-icon {
        color: #e6a23c;
      }
    }
    
    .sidebar-tips {
      padding-top: 12px;
      border-top: 1px solid #ebeef5;
      text-align: center;
    }
  }
  
  .canvas-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: #fff;
      border-radius: 6px;
      margin-bottom: 12px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      
      .toolbar-left {
        display: flex;
        align-items: center;
      }
      
      .toolbar-right {
        display: flex;
        gap: 8px;
      }
    }
    
    .flow-container {
      flex: 1;
      background: #fff;
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
  }
}

.yaml-editor-dialog {
  width: 100%;
  height: 400px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.yaml-editor-detail {
  width: 100%;
  height: 300px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

:deep(.vue-flow) {
  width: 100%;
  height: 100%;
}

:deep(.vue-flow__minimap) {
  background: #f5f7fa;
}

:deep(.el-tree-node__content) {
  height: 32px;
}
</style>
