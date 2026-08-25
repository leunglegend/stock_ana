<template>
  <div class="notification-bell" v-if="userStore.isLoggedIn">
    <el-dropdown
      trigger="click"
      @visible-change="handleDropdownVisible"
      :hide-on-click="false"
    >
      <span class="bell-icon-wrapper">
        <el-badge
          :value="unreadCount > 99 ? '99+' : unreadCount"
          :hidden="unreadCount === 0"
          class="bell-badge"
        >
          <el-icon :size="22" class="bell-icon"><Bell /></el-icon>
        </el-badge>
      </span>

      <template #dropdown>
        <el-dropdown-menu class="notification-dropdown">
          <div class="dropdown-header">
            <span class="header-title">消息通知</span>
            <el-button
              type="primary"
              link
              size="small"
              :disabled="unreadCount === 0"
              @click.stop="handleMarkAllRead"
            >
              全部已读
            </el-button>
          </div>

          <div class="notification-list" v-loading="loading">
            <div
              v-if="!loading && notifications.length === 0"
              class="empty-state"
            >
              <el-empty description="暂无通知" :image-size="60" />
            </div>

            <div
              v-for="item in notifications"
              :key="item.id"
              class="notification-item"
              :class="{ unread: !item.is_read }"
              @click="handleNotificationClick(item)"
            >
              <div class="item-header">
                <span class="item-title">{{ item.title }}</span>
                <span class="item-dot" v-if="!item.is_read"></span>
              </div>
              <div class="item-content">{{ item.content }}</div>
              <div class="item-time">{{ formatTime(item.created_at) }}</div>
            </div>
          </div>

          <div class="dropdown-footer">
            <el-button type="primary" link @click.stop="goToReports">
              查看全部 →
            </el-button>
          </div>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { notificationApi } from '@/api/notification'

const router = useRouter()
const userStore = useUserStore()

const unreadCount = ref(0)
const notifications = ref([])
const loading = ref(false)
let pollTimer = null

// 轮询未读数（60秒一次）
function startPolling() {
  stopPolling()
  fetchUnreadCount()
  pollTimer = setInterval(() => {
    fetchUnreadCount()
  }, 60000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function fetchUnreadCount() {
  try {
    const data = await notificationApi.getUnreadCount()
    unreadCount.value = data.count || 0
  } catch (e) {
    // 静默失败
  }
}

async function fetchNotifications() {
  loading.value = true
  try {
    const data = await notificationApi.getList({ page: 1, page_size: 10 })
    notifications.value = data.items || []
  } catch (e) {
    console.error('获取通知列表失败:', e)
  } finally {
    loading.value = false
  }
}

function handleDropdownVisible(visible) {
  if (visible) {
    fetchNotifications()
  }
}

async function handleNotificationClick(item) {
  // 标记已读
  if (!item.is_read) {
    try {
      await notificationApi.markAsRead(item.id)
      item.is_read = true
      if (unreadCount.value > 0) {
        unreadCount.value--
      }
    } catch (e) {
      console.error('标记已读失败:', e)
    }
  }

  // 跳转到对应页面
  if (item.type === 'report' && item.ref_id) {
    router.push(`/reports/${item.ref_id}`)
  }
}

async function handleMarkAllRead() {
  try {
    await notificationApi.markAllRead()
    unreadCount.value = 0
    notifications.value.forEach(n => (n.is_read = true))
    ElMessage.success('已全部标记为已读')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function goToReports() {
  router.push('/reports')
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  // 1分钟内
  if (diff < 60000) return '刚刚'
  // 1小时内
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  // 今天
  if (date.toDateString() === now.toDateString()) {
    return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  // 昨天
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  // 7天内
  if (diff < 7 * 86400000) {
    return `${Math.floor(diff / 86400000)}天前`
  }
  // 更早
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

// 监听登录状态
watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) {
      startPolling()
    } else {
      stopPolling()
      unreadCount.value = 0
      notifications.value = []
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (userStore.isLoggedIn) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.notification-bell {
  display: flex;
  align-items: center;
}

.bell-icon-wrapper {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  transition: background 0.2s;
}

.bell-icon-wrapper:hover {
  background: #f5f7fa;
}

.bell-icon {
  color: #606266;
}

.bell-badge {
  cursor: pointer;
}

.notification-dropdown {
  width: 340px;
  max-height: 480px;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f2f5;
  flex-shrink: 0;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  max-height: 360px;
}

.empty-state {
  padding: 40px 0;
}

.notification-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f7f8fa;
  transition: background 0.2s;
  position: relative;
}

.notification-item:hover {
  background: #f9fafb;
}

.notification-item.unread {
  background: #f5f3ff;
}

.notification-item.unread:hover {
  background: #ede9fe;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-dot {
  width: 8px;
  height: 8px;
  background: #f56c6c;
  border-radius: 50%;
  flex-shrink: 0;
  margin-left: 8px;
}

.item-content {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}

.item-time {
  font-size: 12px;
  color: #9ca3af;
}

.dropdown-footer {
  text-align: center;
  padding: 10px 16px;
  border-top: 1px solid #f0f2f5;
  flex-shrink: 0;
}
</style>
