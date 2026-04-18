<template>
  <div class="execution-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行详情 #{{ execution?.id }}</span>
          <div class="header-actions">
            <el-button 
              v-if="execution?.status === 'running'" 
              type="warning" 
              @click="cancelExecution"
            >
              取消执行
            </el-button>
            <el-button 
              v-if="execution?.status === 'success'" 
              type="success" 
              @click="downloadReport('html')"
            >
              下载报告
            </el-button>
            <el-button @click="$router.back()">返回</el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="用例名称">{{ execution?.case_name }}</el-descriptions-item>
        <el-descriptions-item label="执行者">{{ execution?.executor_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTypeMap[execution?.status || '']">
            {{ statusMap[execution?.status || ''] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDate(execution?.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatDate(execution?.end_time) }}</el-descriptions-item>
        <el-descriptions-item label="耗时">
          {{ execution?.duration ? execution.duration.toFixed(1) + 's' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(execution?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="execution?.error_message">
          <el-text type="danger">{{ execution.error_message }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>实时日志</span>
          <el-switch v-model="autoScroll" active-text="自动滚动" />
        </div>
      </template>
      
      <div class="log-viewer" ref="logViewerRef">
        <div 
          v-for="(log, index) in logs" 
          :key="index" 
          class="log-line"
          :class="'log-' + log.level.toLowerCase()"
        >
          <span class="log-timestamp">{{ formatLogTime(log.timestamp) }}</span>
          <span class="log-level">[{{ log.level }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
      </div>
    </el-card>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <span>YAML内容</span>
      </template>
      <div class="yaml-content">
        <vue-monaco-editor
          v-model:value="yamlContent"
          language="yaml"
          :options="{ ...editorOptions, readOnly: true }"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { executionApi } from '@/api'
import type { ExecutionDetailResponse } from '@/api/types'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const execution = ref<ExecutionDetailResponse | null>(null)
const logs = ref<Array<{ level: string; message: string; timestamp: string }>>([])
const yamlContent = ref('')
const autoScroll = ref(true)
const logViewerRef = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

const executionId = Number(route.params.id)

const statusMap: Record<string, string> = {
  pending: '等待中',
  running: '运行中',
  success: '成功',
  failed: '失败',
  cancelled: '已取消',
  timeout: '超时'
}

const statusTypeMap: Record<string, string> = {
  pending: 'info',
  running: 'primary',
  success: 'success',
  failed: 'danger',
  cancelled: 'warning',
  timeout: 'danger'
}

const editorOptions = {
  minimap: { enabled: false },
  fontSize: 13,
  lineNumbers: 'on' as const,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  readOnly: true
}

function formatDate(date?: string | null) {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function formatLogTime(timestamp: string) {
  return dayjs(timestamp).format('HH:mm:ss')
}

async function loadExecution() {
  try {
    execution.value = await executionApi.get(executionId)
    yamlContent.value = execution.value.yaml_content || ''
    logs.value = execution.value.logs.map(l => ({
      level: l.level,
      message: l.message,
      timestamp: l.timestamp
    }))
    
    if (execution.value.status === 'running' || execution.value.status === 'pending') {
      connectWebSocket()
    }
  } catch (e) {
    ElMessage.error('加载执行详情失败')
    router.push('/executions')
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws/logs/${executionId}`)
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.type === 'status') {
        if (execution.value) {
          execution.value.status = data.status
        }
        if (data.status !== 'running' && data.status !== 'pending') {
          ws?.close()
        }
      } else {
        logs.value.push({
          level: data.level,
          message: data.message,
          timestamp: data.timestamp
        })
        
        if (autoScroll.value) {
          nextTick(() => {
            if (logViewerRef.value) {
              logViewerRef.value.scrollTop = logViewerRef.value.scrollHeight
            }
          })
        }
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
  
  ws.onclose = () => {
    ws = null
  }
}

async function cancelExecution() {
  try {
    await ElMessageBox.confirm('确定要取消该执行吗？', '确认取消')
    await executionApi.cancel(executionId)
    ElMessage.success('已取消执行')
    if (execution.value) {
      execution.value.status = 'cancelled'
    }
    ws?.close()
  } catch (e) {
    // cancelled
  }
}

function downloadReport(format: string) {
  const url = executionApi.downloadReport(executionId, format)
  window.open(url, '_blank')
}

watch(logs, () => {
  if (autoScroll.value) {
    nextTick(() => {
      if (logViewerRef.value) {
        logViewerRef.value.scrollTop = logViewerRef.value.scrollHeight
      }
    })
  }
}, { deep: true })

onMounted(() => {
  loadExecution()
})

onUnmounted(() => {
  ws?.close()
})
</script>

<style scoped lang="scss">
.execution-detail {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .log-viewer {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 16px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    overflow: auto;
    max-height: 500px;
    
    .log-line {
      margin-bottom: 4px;
      
      .log-timestamp {
        color: #6a9955;
        margin-right: 8px;
      }
      
      .log-level {
        margin-right: 8px;
      }
      
      .log-message {
        white-space: pre-wrap;
        word-break: break-all;
      }
      
      &.log-info .log-level {
        color: #4ec9b0;
      }
      
      &.log-warning .log-level {
        color: #dcdcaa;
      }
      
      &.log-error .log-level {
        color: #f14c4c;
      }
    }
    
    .log-empty {
      color: #6a9955;
      text-align: center;
      padding: 20px;
    }
  }
  
  .yaml-content {
    height: 400px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    overflow: hidden;
  }
}
</style>
