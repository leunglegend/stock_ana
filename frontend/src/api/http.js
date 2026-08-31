/**
 * 通用 axios 实例
 * 自动注入 token，401 自动登出并触发登录弹窗
 */
import axios from 'axios'
import { useUserStore } from '@/store/user'

const LOGIN_REQUIRED_EVENT = 'show-login'
const LOGIN_PROMPT_RESET_EVENT = 'auth-login-prompt-reset'
let loginPromptActive = false

if (typeof window !== 'undefined') {
  window.addEventListener(LOGIN_PROMPT_RESET_EVENT, () => {
    loginPromptActive = false
  })
}

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

function isAuthEndpoint(url = '') {
  return url.includes('/auth/login') || url.includes('/auth/register')
}

function getCurrentRoutePath() {
  if (typeof window === 'undefined') {
    return ''
  }

  return `${window.location.pathname}${window.location.search}${window.location.hash}`
}

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
      if (error.config?.skipAuthRedirect || isAuthEndpoint(error.config?.url)) {
        return Promise.reject(error)
      }

      const userStore = useUserStore()
      const targetPath = getCurrentRoutePath()
      userStore.handleUnauthorized(targetPath)

      if (!loginPromptActive) {
        loginPromptActive = true
        window.dispatchEvent(new CustomEvent(LOGIN_REQUIRED_EVENT, {
          detail: { targetPath },
        }))
      }
    }

    return Promise.reject(error)
  }
)

export default http
