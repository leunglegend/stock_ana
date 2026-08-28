<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <el-icon :size="28" color="#8b5cf6"><TrendCharts /></el-icon>
        <span class="logo-text">智能分析</span>
      </div>

      <nav class="nav-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-text">{{ item.title }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <!-- 未登录：显示登录按钮 -->
        <div v-if="!userStore.isLoggedIn" class="user-login">
          <el-button type="primary" plain style="width: 100%" @click="openLogin">
            <el-icon><User /></el-icon>
            <span class="nav-text">点击登录</span>
          </el-button>
        </div>

        <!-- 已登录：显示用户信息 + 下拉菜单 -->
        <el-dropdown v-else trigger="click" @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="32" icon="User" />
            <div class="user-detail">
              <div class="user-name">{{ userStore.username }}</div>
              <div class="user-desc">已登录</div>
            </div>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main">
      <!-- 顶部栏 -->
      <div class="top-bar">
        <div class="top-bar-right">
          <NotificationBell />
        </div>
      </div>

      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, RouterLink, RouterView } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts, Odometer, Search, Star, DataAnalysis, Document, User, ArrowDown, SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import NotificationBell from './NotificationBell.vue'

const route = useRoute()
const userStore = useUserStore()

const menuItems = computed(() => [
  { path: '/', title: '市场概览', icon: 'Odometer' },
  { path: '/search', title: '搜索个股', icon: 'Search' },
  { path: '/watchlist', title: '自选股', icon: 'Star' },
  { path: '/board', title: '板块监控', icon: 'DataAnalysis' },
  { path: '/reports', title: '复盘报告', icon: 'Document' },
])

function isActive(path) {
  if (path === '/reports') {
    return route.path === '/reports' || route.path.startsWith('/reports/')
  }
  return route.path === path
}

function openLogin() {
  window.dispatchEvent(new CustomEvent('show-login'))
}

async function handleCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning',
      })
      userStore.logout()
      ElMessage.success('已退出登录')
    } catch (e) {
      // 用户取消
    }
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f2f5;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.5px;
}

.nav-menu {
  flex: 1;
  padding: 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: #606266;
  font-size: 14px;
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f5f7fa;
  color: #303133;
}

.nav-item.active {
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #f0f2f5;
}

.user-login {
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-login .el-button {
  justify-content: center;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-detail {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* 主内容区 */
.main {
  flex: 1;
  margin-left: 220px;
  padding: 24px 28px;
  min-height: 100vh;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 页面过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px;
  }
  .logo-text, .nav-text, .user-detail {
    display: none;
  }
  .main {
    margin-left: 64px;
    padding: 16px;
  }
}
</style>
