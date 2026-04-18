<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409EFF">
              <el-icon size="28"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalCases }}</div>
              <div class="stat-label">用例总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67C23A">
              <el-icon size="28"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.successCount }}</div>
              <div class="stat-label">执行成功</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #F56C6C">
              <el-icon size="28"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.failedCount }}</div>
              <div class="stat-label">执行失败</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #E6A23C">
              <el-icon size="28"><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.scheduleCount }}</div>
              <div class="stat-label">定时任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>最近执行记录</span>
          </template>
          <el-table :data="recentExecutions" style="width: 100%">
            <el-table-column prop="case_name" label="用例名称" min-width="180" />
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
            <el-table-column prop="created_at" label="执行时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/cases/create')">
              <el-icon><Plus /></el-icon>
              创建用例
            </el-button>
            <el-button @click="$router.push('/cases')">
              <el-icon><Document /></el-icon>
              查看用例
            </el-button>
            <el-button @click="$router.push('/schedules')">
              <el-icon><Timer /></el-icon>
              定时任务
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { caseApi, executionApi, scheduleApi } from '@/api'
import dayjs from 'dayjs'

const stats = ref({
  totalCases: 0,
  successCount: 0,
  failedCount: 0,
  scheduleCount: 0
})

const recentExecutions = ref<any[]>([])

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

async function loadStats() {
  try {
    const [casesRes, executionsRes, schedulesRes] = await Promise.all([
      caseApi.getList({ page_size: 1 }),
      executionApi.getList({ page_size: 100 }),
      scheduleApi.getList({ page_size: 1 })
    ])
    
    stats.value.totalCases = casesRes.total
    stats.value.scheduleCount = schedulesRes.total
    
    const executions = executionsRes.items
    stats.value.successCount = executions.filter((e: any) => e.status === 'success').length
    stats.value.failedCount = executions.filter((e: any) => e.status === 'failed').length
    
    recentExecutions.value = executions.slice(0, 10)
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.dashboard {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      
      .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
      }
      
      .stat-info {
        margin-left: 16px;
        
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
  
  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .el-button {
      width: 100%;
      justify-content: flex-start;
    }
  }
}
</style>
