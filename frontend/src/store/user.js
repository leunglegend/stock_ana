import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi } from '@/api/auth'

const TOKEN_KEY = 'stock_user_token'
const USER_KEY = 'stock_user_info'

let initializePromise = null

function syncToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
    return
  }
  localStorage.removeItem(TOKEN_KEY)
}

function clearLegacyUserInfo() {
  localStorage.removeItem(USER_KEY)
}

function openLoginModal() {
  window.dispatchEvent(new CustomEvent('show-login'))
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(null)
  const authReady = ref(false)
  const pendingRoute = ref('')

  clearLegacyUserInfo()

  const isLoggedIn = computed(() => Boolean(token.value && userInfo.value))
  const username = computed(() => userInfo.value?.username || '')

  function setPendingRoute(route) {
    pendingRoute.value = route || ''
  }

  function consumePendingRoute() {
    const route = pendingRoute.value
    pendingRoute.value = ''
    return route
  }

  function clearPendingRoute() {
    pendingRoute.value = ''
  }

  function clearAuth() {
    token.value = ''
    userInfo.value = null
    syncToken('')
    clearLegacyUserInfo()
  }

  async function fetchUserInfo(options = {}) {
    const { throwOnError = false } = options
    if (!token.value) return null
    try {
      const response = await authApi.getMe()
      userInfo.value = response.data
      return response.data
    } catch (error) {
      clearAuth()
      if (throwOnError) {
        throw error
      }
      return null
    }
  }

  async function initializeAuth() {
    if (authReady.value) return userInfo.value
    if (initializePromise) return initializePromise

    initializePromise = (async () => {
      clearLegacyUserInfo()
      if (!token.value) {
        authReady.value = true
        return null
      }

      const user = await fetchUserInfo()
      authReady.value = true
      return user
    })().finally(() => {
      initializePromise = null
    })

    return initializePromise
  }

  function requestLogin(route) {
    setPendingRoute(route)
    openLoginModal()
  }

  function handleUnauthorized(route) {
    if (route) setPendingRoute(route)
    clearAuth()
    authReady.value = true
  }

  async function login(usernameValue, password) {
    const response = await authApi.login(usernameValue, password)
    const { access_token } = response.data
    token.value = access_token
    userInfo.value = null
    authReady.value = false
    syncToken(access_token)
    clearLegacyUserInfo()

    try {
      const user = await fetchUserInfo({ throwOnError: true })
      authReady.value = true
      return user
    } catch (error) {
      authReady.value = true
      throw error
    }
  }

  async function register(usernameValue, password) {
    const response = await authApi.register(usernameValue, password)
    return response.data
  }

  function logout() {
    clearAuth()
    authReady.value = true
  }

  return {
    token,
    userInfo,
    authReady,
    pendingRoute,
    isLoggedIn,
    username,
    setPendingRoute,
    consumePendingRoute,
    clearPendingRoute,
    requestLogin,
    handleUnauthorized,
    login,
    register,
    logout,
    fetchUserInfo,
    initializeAuth,
  }
})
