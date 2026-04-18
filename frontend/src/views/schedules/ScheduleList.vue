<template>
  <div class="schedule-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建定时任务
          </el-button>
        </div>
      </template>
      
      <el-table :data="schedules" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column prop="case_name" label="关联用例" width="180" />
        <el-table-column prop="cron_expr" label="Cron表达式" width="150">
          <template #default="{ row }">
            <el-tooltip :content="getCronDescription(row.cron_expr)">
              <span>{{ row.cron_expr }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="next_run" label="下次执行" width="180">
          <template #default="{ row }">
            {{ formatDate(row.next_run) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_run" label="上次执行" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_run) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_status" label="上次状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.last_status" :type="statusTypeMap[row.last_status]" size="small">
              {{ statusMap[row.last_status] }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="toggleSchedule(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" @click="editSchedule(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="deleteSchedule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadSchedules"
        @current-change="loadSchedules"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
    
    <el-dialog v-model="showCreateDialog" :title="editingSchedule ? '编辑定时任务' : '新建定时任务'" width="500px">
      <el-form :model="scheduleForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="scheduleForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="关联用例" prop="case_id">
          <el-select v-model="scheduleForm.case_id" placeholder="选择用例" filterable style="width: 100%">
            <el-option v-for="c in cases" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式" prop="cron_expr">
          <el-input v-model="scheduleForm.cron_expr" placeholder="如: 0 9 * * * (每天9点)" />
          <div class="cron-help">
            <el-text size="small" type="info">
              格式: 分 时 日 月 周 (如: 0 9 * * * 表示每天9点)
            </el-text>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="saveSchedule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scheduleApi, caseApi } from '@/api'
import type { ScheduleResponse, CaseResponse } from '@/api/types'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import cronParser from 'cron-parser'

const schedules = ref<ScheduleResponse[]>([])
const cases = ref<CaseResponse[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const showCreateDialog = ref(false)
const editingSchedule = ref<ScheduleResponse | null>(null)
const formRef = ref<FormInstance>()

const scheduleForm = reactive({
  name: '',
  case_id: null as number | null,
  cron_expr: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  case_id: [{ required: true, message: '请选择用例', trigger: 'change' }],
  cron_expr: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }]
}

const statusMap: Record<string, string> = {
  pending: '等待中',
  running: '运行中',
  success: '成功',
  failed: '失败',
  cancelled: '已取消'
}

const statusTypeMap: Record<string, string> = {
  pending: 'info',
  running: 'primary',
  success: 'success',
  failed: 'danger',
  cancelled: 'warning'
}

function formatDate(date?: string | null) {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getCronDescription(cronExpr: string): string {
  try {
    const interval = cronParser.parseExpression(cronExpr)
    const next = interval.next()
    return `下次执行: ${dayjs(next.toDate()).format('YYYY-MM-DD HH:mm:ss')}`
  } catch {
    return '无效的Cron表达式'
  }
}

async function loadSchedules() {
  loading.value = true
  try {
    const response = await scheduleApi.getList({
      page: currentPage.value,
      page_size: pageSize.value
    })
    schedules.value = response.items
    total.value = response.total
  } finally {
    loading.value = false
  }
}

async function loadCases() {
  const response = await caseApi.getList({ page_size: 1000 })
  cases.value = response.items
}

function closeDialog() {
  showCreateDialog.value = false
  editingSchedule.value = null
  scheduleForm.name = ''
  scheduleForm.case_id = null
  scheduleForm.cron_expr = ''
  formRef.value?.resetFields()
}

function editSchedule(schedule: ScheduleResponse) {
  editingSchedule.value = schedule
  scheduleForm.name = schedule.name
  scheduleForm.case_id = schedule.case_id
  scheduleForm.cron_expr = schedule.cron_expr
  showCreateDialog.value = true
}

async function saveSchedule() {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  try {
    if (editingSchedule.value) {
      await scheduleApi.update(editingSchedule.value.id, {
        name: scheduleForm.name,
        cron_expr: scheduleForm.cron_expr
      })
      ElMessage.success('更新成功')
    } else {
      await scheduleApi.create({
        name: scheduleForm.name,
        case_id: scheduleForm.case_id!,
        cron_expr: scheduleForm.cron_expr
      })
      ElMessage.success('创建成功')
    }
    closeDialog()
    loadSchedules()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function toggleSchedule(schedule: ScheduleResponse) {
  try {
    await scheduleApi.toggle(schedule.id)
    ElMessage.success(schedule.is_active ? '已禁用' : '已启用')
    loadSchedules()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function deleteSchedule(schedule: ScheduleResponse) {
  try {
    await ElMessageBox.confirm(`确定要删除定时任务 "${schedule.name}" 吗？`, '确认删除', { type: 'warning' })
    await scheduleApi.delete(schedule.id)
    ElMessage.success('删除成功')
    loadSchedules()
  } catch (e) {
    // cancelled
  }
}

onMounted(() => {
  loadSchedules()
  loadCases()
})
</script>

<style scoped lang="scss">
.schedule-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .cron-help {
    margin-top: 4px;
  }
}
</style>
