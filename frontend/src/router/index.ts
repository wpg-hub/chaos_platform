import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      redirect: '/dashboard',
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '首页', icon: 'HomeFilled' }
        },
        {
          path: 'cases',
          name: 'Cases',
          component: () => import('@/views/workflow/WorkflowEditor.vue'),
          meta: { title: '用例管理', icon: 'Share' }
        },
        {
          path: 'executions',
          name: 'Executions',
          component: () => import('@/views/executions/ExecutionList.vue'),
          meta: { title: '执行中心', icon: 'VideoPlay' }
        },
        {
          path: 'executions/:id',
          name: 'ExecutionDetail',
          component: () => import('@/views/executions/ExecutionDetail.vue'),
          meta: { title: '执行详情', hidden: true }
        },
        {
          path: 'history',
          name: 'History',
          component: () => import('@/views/executions/ExecutionList.vue'),
          meta: { title: '历史记录', icon: 'Clock' }
        },
        {
          path: 'schedules',
          name: 'Schedules',
          component: () => import('@/views/schedules/ScheduleList.vue'),
          meta: { title: '定时任务', icon: 'Timer' }
        },
        {
          path: 'users',
          name: 'Users',
          component: () => import('@/views/system/UserManagement.vue'),
          meta: { title: '用户管理', icon: 'User', roles: ['admin'] }
        }
      ]
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
