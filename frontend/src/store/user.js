/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

const TOKEN_KEY = 'stock_user_token'
const USER_KEY = 'stock_user_info'

export const useUserStore = defineStore('user', () => {
  // state
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

  // getters
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const username = computed(() => userInfo.value?.username || '')

  // actions
  async function login(username, password) {
    const res = await authApi.login(username, password)
    const { access_token, user } = res.data
    token.value = access_token
    userInfo.value = user
    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return user
  }

  async function register(username, password) {
    const res = await authApi.register(username, password)
    return res.data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    try {
      const res = await authApi.getMe()
      userInfo.value = res.data
      localStorage.setItem(USER_KEY, JSON.stringify(res.data))
      return res.data
    } catch (e) {
      // token 无效，清除
      logout()
      return null
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    login,
    register,
    logout,
    fetchUserInfo,
  }
})
