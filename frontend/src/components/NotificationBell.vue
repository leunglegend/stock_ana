<template>
  <div class="notification-bell" v-if="userStore.isLoggedIn">
    <el-dropdown
      trigger="click"
      @visible-change="handleDropdownVisible"
      :hide-on-click="false"
    >
      <button class="bell-icon-wrapper" type="button" aria-label="打开通知">
        <el-badge
          :value="unreadCount > 99 ? '99+' : unreadCount"
          :hidden="unreadCount === 0"
          class="bell-badge"
        >
          <el-icon :size="22" class="bell-icon"><Bell /></el-icon>
        </el-badge>
      </button>

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
              v-if="!loading && notificationError"
              class="error-state"
              role="alert"
            >
              <p>{{ notificationError }}</p>
              <el-button type="primary" size="small" @click.stop="retryNotifications">
                重新加载
              </el-button>
            </div>

            <div
              v-else-if="!loading && notifications.length === 0"
              class="empty-state"
            >
              <el-empty description="暂无通知" :image-size="60" />
            </div>

            <button
              v-for="item in notifications"
              :key="item.id"
              class="notification-item"
              :class="{ unread: !item.is_read }"
              type="button"
              @click="handleNotificationClick(item)"
            >
              <div class="item-header">
                <span class="item-title">{{ item.title }}</span>
                <span class="item-dot" v-if="!item.is_read" aria-hidden="true"></span>
                <span v-if="!item.is_read" class="sr-only">未读</span>
              </div>
              <div class="item-content">{{ item.content }}</div>
              <div class="item-time">{{ formatNotificationTime(item.created_at) }}</div>
            </button>
          </div>

          <p class="sr-only" aria-live="polite">{{ liveMessage }}</p>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { Bell } from '@element-plus/icons-vue'
import { useNotifications } from '@/composables/useNotifications'

const {
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
} = useNotifications()
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
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
  padding: 0;
  border: 0;
  background: transparent;
}

.bell-icon-wrapper:hover {
  background: var(--surface-panel-muted);
}

.bell-icon {
  color: var(--text-secondary);
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
  background: var(--surface-panel);
  color: var(--text-primary);
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  max-height: 360px;
}

.empty-state {
  padding: 40px 0;
}

.error-state {
  display: grid;
  justify-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-8) var(--spacing-4);
  color: var(--text-secondary);
  text-align: center;
}

.error-state p { margin: 0; }

.notification-item {
  width: 100%;
  display: block;
  border: 0;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-subtle);
  transition: background var(--transition-fast);
  position: relative;
  background: transparent;
  text-align: left;
}

.notification-item:hover {
  background: var(--surface-panel-muted);
}

.notification-item.unread {
  background: var(--color-primary-50);
}

.notification-item.unread:hover {
  background: var(--color-primary-100);
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
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-dot {
  width: 8px;
  height: 8px;
  background: var(--color-up-500);
  border-radius: 50%;
  flex-shrink: 0;
  margin-left: 8px;
}

.item-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}

.item-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 420px) {
  .notification-dropdown {
    width: calc(100vw - 24px);
  }
}
</style>
