/**
 * 通用 axios 实例
 * 自动注入 token，401 自动登出并触发登录弹窗
 */
import axios from 'axios'
import { useUserStore } from '@/store/user'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：注入 token
http.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：401 清除登录状态
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      window.dispatchEvent(new CustomEvent('show-login'))
    }
    return Promise.reject(error)
  }
)

export default http
