<template>
  <div class="execution-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行历史</span>
          <div class="header-actions">
            <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">
              批量删除
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="filter-bar">
        <el-select v-model="filterStatus" placeholder="执行状态" clearable @change="loadExecutions">
          <el-option label="全部状态" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </div>
      
      <el-table 
        :data="executions" 
        v-loading="loading" 
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="case_name" label="用例名称" min-width="180">
          <template #default="{ row }">
            <el-link @click="viewDetail(row.id)">{{ row.case_name || '-' }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTypeMap[row.status]">
              {{ statusMap[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executor_name" label="执行者" width="100" />
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration ? row.duration.toFixed(1) + 's' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row.id)">详情</el-button>
            <el-button 
              v-if="row.status === 'running'" 
              type="warning" 
              size="small" 
              @click="cancelExecution(row)"
            >
              取消
            </el-button>
            <el-button 
              v-if="row.status === 'success'" 
              type="success" 
              size="small" 
              @click="downloadReport(row.id, 'html')"
            >
              报告
            </el-button>
            <el-button type="danger" size="small" @click="deleteExecution(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadExecutions"
        @current-change="loadExecutions"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { executionApi } from '@/api'
import type { ExecutionResponse } from '@/api/types'
import dayjs from 'dayjs'

const router = useRouter()

const executions = ref<ExecutionResponse[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')
const selectedIds = ref<number[]>([])

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

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

async function loadExecutions() {
  loading.value = true
  try {
    const response = await executionApi.getList({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined
    })
    executions.value = response.items
    total.value = response.total
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(selection: ExecutionResponse[]) {
  selectedIds.value = selection.map(e => e.id)
}

function viewDetail(id: number) {
  router.push(`/executions/${id}`)
}

async function cancelExecution(execution: ExecutionResponse) {
  try {
    await ElMessageBox.confirm('确定要取消该执行吗？', '确认取消')
    await executionApi.cancel(execution.id)
    ElMessage.success('已取消执行')
    loadExecutions()
  } catch (e) {
    // cancelled
  }
}

async function deleteExecution(execution: ExecutionResponse) {
  try {
    await ElMessageBox.confirm('确定要删除该执行记录吗？', '确认删除', { type: 'warning' })
    await executionApi.delete(execution.id)
    ElMessage.success('删除成功')
    loadExecutions()
  } catch (e) {
    // cancelled
  }
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 条记录吗？`, '确认删除', { type: 'warning' })
    await executionApi.deleteBatch(selectedIds.value)
    ElMessage.success('删除成功')
    loadExecutions()
  } catch (e) {
    // cancelled
  }
}

function downloadReport(id: number, format: string) {
  const url = executionApi.downloadReport(id, format)
  window.open(url, '_blank')
}

onMounted(() => {
  loadExecutions()
})
</script>

<style scoped lang="scss">
.execution-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .filter-bar {
    margin-bottom: 16px;
  }
}
</style>
