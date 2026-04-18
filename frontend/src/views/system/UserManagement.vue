<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建用户
          </el-button>
        </div>
      </template>
      
      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="roleTypeMap[row.role]">{{ roleMap[row.role] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="deleteUser(row)"
              :disabled="row.id === currentUserId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showCreateDialog" :title="editingUser ? '编辑用户' : '新建用户'" width="500px">
      <el-form :model="userForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username" v-if="!editingUser">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-else>
          <el-input v-model="userForm.password" type="password" placeholder="留空则不修改密码" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="只读用户" value="readonly" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active" v-if="editingUser">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { UserResponse } from '@/api/types'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

const users = ref<UserResponse[]>([])
const loading = ref(false)

const showCreateDialog = ref(false)
const editingUser = ref<UserResponse | null>(null)
const formRef = ref<FormInstance>()

const userForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const roleMap: Record<string, string> = {
  admin: '管理员',
  user: '普通用户',
  readonly: '只读用户'
}

const roleTypeMap: Record<string, string> = {
  admin: 'danger',
  user: 'primary',
  readonly: 'info'
}

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

async function loadUsers() {
  loading.value = true
  try {
    users.value = await userApi.getList()
  } finally {
    loading.value = false
  }
}

function closeDialog() {
  showCreateDialog.value = false
  editingUser.value = null
  userForm.username = ''
  userForm.email = ''
  userForm.password = ''
  userForm.role = 'user'
  userForm.is_active = true
  formRef.value?.resetFields()
}

function editUser(user: UserResponse) {
  editingUser.value = user
  userForm.username = user.username
  userForm.email = user.email || ''
  userForm.password = ''
  userForm.role = user.role
  userForm.is_active = user.is_active
  showCreateDialog.value = true
}

async function saveUser() {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  try {
    if (editingUser.value) {
      const updateData: any = {
        email: userForm.email || undefined,
        role: userForm.role,
        is_active: userForm.is_active
      }
      if (userForm.password) {
        updateData.password = userForm.password
      }
      await userApi.update(editingUser.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      await userApi.create({
        username: userForm.username,
        email: userForm.email || undefined,
        password: userForm.password,
        role: userForm.role
      })
      ElMessage.success('创建成功')
    }
    closeDialog()
    loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function deleteUser(user: UserResponse) {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${user.username}" 吗？`, '确认删除', { type: 'warning' })
    await userApi.delete(user.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e) {
    // cancelled
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped lang="scss">
.user-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
