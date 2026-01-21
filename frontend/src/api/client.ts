import axios from 'axios'
import type { AxiosError } from 'axios'

export function apiBaseUrl(): string {
  // Vite env: VITE_API_BASE_URL=http://localhost:8000
  return (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'
}

export const api = axios.create({
  baseURL: apiBaseUrl() + '/api/v1',
  timeout: 20000,
})

// 请求拦截：自动附加 Bearer Token
api.interceptors.request.use(config => {
  const token = window.localStorage.getItem('acm_tb_access_token')
  if (token) {
    config.headers = config.headers ?? {}
    if (!config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
  }
  return config
})

// 响应拦截：401 统一跳转登录
api.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      window.localStorage.removeItem('acm_tb_access_token')
      const current = window.location.pathname + window.location.search
      if (!current.startsWith('/login')) {
        const redirect = encodeURIComponent(current)
        window.location.href = `/login?redirect=${redirect}`
      }
    }
    return Promise.reject(error)
  },
)

