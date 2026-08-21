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
          :class="{ active: route.path === item.path }"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-text">{{ item.title }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <el-avatar :size="32" icon="User" />
          <div class="user-detail">
            <div class="user-name">投资者</div>
            <div class="user-desc">VIP 会员</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main">
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
import {
  TrendCharts, Odometer, Star, DataAnalysis, User,
} from '@element-plus/icons-vue'

const route = useRoute()

const menuItems = computed(() => [
  { path: '/', title: '市场概览', icon: 'Odometer' },
  { path: '/watchlist', title: '自选股', icon: 'Star' },
  { path: '/board', title: '板块监控', icon: 'DataAnalysis' },
])
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

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
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
