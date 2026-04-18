import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserResponse, LoginRequest } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserResponse | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isUser = computed(() => user.value?.role === 'user' || user.value?.role === 'admin')

  async function login(credentials: LoginRequest) {
    const response = await authApi.login(credentials)
    token.value = response.access_token
    localStorage.setItem('token', response.access_token)
    await fetchUser()
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (e) {
      // ignore
    }
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchUser() {
    if (token.value) {
      try {
        user.value = await authApi.getMe()
      } catch (e) {
        logout()
      }
    }
  }

  if (token.value) {
    fetchUser()
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isUser,
    login,
    logout,
    fetchUser
  }
})
