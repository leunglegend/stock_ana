import { onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'

import { notificationApi } from '@/api/notification'
import { useUserStore } from '@/store/user'

const POLL_INTERVAL = 60000
const LIST_PARAMS = { page: 1, page_size: 10 }
const REPORT_TYPE = 'report'

function createNotificationSessionGuard() {
  let generation = 0

  function capture(userStore) {
    return {
      generation,
      token: userStore.token,
      userId: userStore.userInfo?.id,
    }
  }

  function invalidate() {
    generation += 1
  }

  function isCurrent(session, userStore) {
    return session.generation === generation
      && userStore.isLoggedIn
      && userStore.token === session.token
      && userStore.userInfo?.id === session.userId
  }

  return { capture, invalidate, isCurrent }
}

function formatNotificationTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (date.toDateString() === now.toDateString()) {
    return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  if (diff < 7 * 86400000) return `${Math.floor(diff / 86400000)}天前`
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

export function useNotifications() {
  const router = useRouter()
  const userStore = useUserStore()
  const unreadCount = ref(0)
  const notifications = ref([])
  const loading = ref(false)
  const notificationError = ref('')
  const liveMessage = ref('')
  const sessionGuard = createNotificationSessionGuard()
  let pollTimer = null
  let listRequestId = 0

  function stopPolling() {
    if (!pollTimer) return
    clearInterval(pollTimer)
    pollTimer = null
  }

  function resetState() {
    listRequestId += 1
    unreadCount.value = 0
    notifications.value = []
    loading.value = false
    notificationError.value = ''
    liveMessage.value = ''
  }

  async function fetchUnreadCount() {
    const session = sessionGuard.capture(userStore)
    try {
      const data = await notificationApi.getUnreadCount()
      if (!sessionGuard.isCurrent(session, userStore)) return
      unreadCount.value = data.count || 0
    } catch {}
  }

  function startPolling() {
    stopPolling()
    void fetchUnreadCount()
    pollTimer = window.setInterval(fetchUnreadCount, POLL_INTERVAL)
  }

  async function fetchNotifications() {
    const requestId = ++listRequestId
    const session = sessionGuard.capture(userStore)
    loading.value = true
    notificationError.value = ''
    try {
      const data = await notificationApi.getList(LIST_PARAMS)
      if (!sessionGuard.isCurrent(session, userStore) || requestId !== listRequestId) return
      notifications.value = data.items || []
    } catch (error) {
      if (!sessionGuard.isCurrent(session, userStore) || requestId !== listRequestId) return
      console.error('获取通知列表失败:', error)
      notificationError.value = '通知加载失败，请重试'
    } finally {
      if (sessionGuard.isCurrent(session, userStore) && requestId === listRequestId) {
        loading.value = false
      }
    }
  }

  function retryNotifications() {
    return fetchNotifications()
  }

  async function markNotificationRead(item) {
    if (item.is_read) return
    let session = sessionGuard.capture(userStore)
    session = arguments[1] ?? session
    try {
      await notificationApi.markAsRead(item.id)
      const currentItem = notifications.value.find(({ id }) => id === item.id)
      if (!sessionGuard.isCurrent(session, userStore) || !currentItem) return
      currentItem.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      liveMessage.value = '通知已标记为已读'
    } catch (error) {
      const currentItem = notifications.value.find(({ id }) => id === item.id)
      if (!sessionGuard.isCurrent(session, userStore) || !currentItem) return
      console.error('标记已读失败:', error)
    }
  }

  async function handleNotificationClick(item) {
    const session = sessionGuard.capture(userStore)
    const currentItem = notifications.value.find(({ id }) => id === item.id)
    if (!sessionGuard.isCurrent(session, userStore) || !currentItem) return
    await markNotificationRead(currentItem, session)
    if (!sessionGuard.isCurrent(session, userStore) || !notifications.value.includes(currentItem)) return
    if (currentItem.type === REPORT_TYPE && currentItem.ref_id) await router.push(`/reports/${currentItem.ref_id}`)
  }

  async function handleMarkAllRead() {
    const session = sessionGuard.capture(userStore)
    try {
      await notificationApi.markAllRead()
      if (!sessionGuard.isCurrent(session, userStore)) return
      unreadCount.value = 0
      notifications.value.forEach((item) => { item.is_read = true })
      liveMessage.value = '全部通知已标记为已读'
      ElMessage.success('已全部标记为已读')
    } catch {
      if (!sessionGuard.isCurrent(session, userStore)) return
      ElMessage.error('操作失败')
    }
  }

  function handleDropdownVisible(visible) {
    if (visible) void fetchNotifications()
  }

  watch(
    () => userStore.isLoggedIn,
    (loggedIn) => {
      sessionGuard.invalidate()
      if (loggedIn) startPolling()
      else {
        stopPolling()
        resetState()
      }
    },
    { immediate: true }
  )

  onUnmounted(stopPolling)

  return {
    userStore,
    unreadCount,
    notifications,
    loading,
    notificationError,
    liveMessage,
    formatNotificationTime,
    retryNotifications,
    handleDropdownVisible,
    handleNotificationClick,
    handleMarkAllRead,
  }
}
