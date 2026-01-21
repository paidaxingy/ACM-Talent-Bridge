import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export type UserRole = 'student' | 'admin'

export interface CurrentUser {
  user_id: number
  username: string
  role: UserRole
}

const ACCESS_TOKEN_KEY = 'acm_tb_access_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<CurrentUser | null>(null)
  const loadingMe = ref(false)

  function setToken(next: string | null) {
    token.value = next
    if (next) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, next)
    } else {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY)
    }
  }

  function loadTokenFromStorage() {
    const stored = window.localStorage.getItem(ACCESS_TOKEN_KEY)
    if (stored) {
      token.value = stored
    }
  }

  async function fetchMe() {
    if (!token.value) {
      user.value = null
      window.localStorage.removeItem('acm_tb_user_role')
      return
    }
    loadingMe.value = true
    try {
      const { data } = await api.get<CurrentUser>('/auth/me')
      user.value = data
      window.localStorage.setItem('acm_tb_user_role', data.role)
    } catch {
      // token 失效，清理本地状态
      setToken(null)
      user.value = null
      window.localStorage.removeItem('acm_tb_user_role')
    } finally {
      loadingMe.value = false
    }
  }

  async function login(payload: { username: string; password: string }) {
    const { data } = await api.post<{ access_token: string; token_type: string }>('/auth/login', payload)
    setToken(data.access_token)
    await fetchMe()
  }

  async function register(payload: { username: string; password: string }) {
    // 注册本身不返回 token：成功后再走一次登录，保证“注册并登录”体验
    await api.post('/auth/register', payload)
    await login(payload)
  }

  function logout() {
    setToken(null)
    user.value = null
    window.localStorage.removeItem('acm_tb_user_role')
  }

  return {
    token,
    user,
    loadingMe,
    setToken,
    loadTokenFromStorage,
    fetchMe,
    login,
    register,
    logout,
  }
})

