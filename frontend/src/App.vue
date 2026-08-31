<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Layout from './components/Layout.vue'
import LoginModal from './components/LoginModal.vue'
import { useUserStore } from './store/user'

const route = useRoute()
const userStore = useUserStore()

const isProtectedRoute = computed(() => route.matched.some(record => record.meta.requiresAuth))
const shouldHideLayout = computed(() => {
  return userStore.authReady && isProtectedRoute.value && !userStore.isLoggedIn
})
const blockedRouteTitle = computed(() => route.meta.title || '目标页面')

onMounted(() => {
  userStore.initializeAuth()
})

function reopenLogin() {
  userStore.requestLogin(userStore.pendingRoute || route.fullPath)
}
</script>

<template>
  <div v-if="!userStore.authReady" class="app-boot" aria-busy="true" aria-live="polite">
    <div class="app-boot__panel">
      <p class="app-boot__label">正在恢复登录状态</p>
      <p class="app-boot__hint">稍候进入研究工作台</p>
    </div>
  </div>
  <div
    v-else-if="shouldHideLayout"
    class="app-guard"
    role="status"
    aria-live="polite"
  >
    <div class="app-guard__panel">
      <p class="app-guard__label">需要登录后继续访问</p>
      <p class="app-guard__hint">{{ blockedRouteTitle }} 已暂时隐藏，登录后会重新加载数据。</p>
      <el-button type="primary" @click="reopenLogin">继续登录</el-button>
    </div>
  </div>
  <Layout v-else />
  <LoginModal />
</template>

<style scoped>
.app-boot {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--surface-page);
}

.app-boot__panel {
  min-width: 240px;
  padding: var(--spacing-5);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-primary);
  box-shadow: var(--shadow-sm);
  text-align: center;
}

.app-boot__label {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.app-boot__hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

.app-guard {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--surface-page);
}

.app-guard__panel {
  max-width: 420px;
  padding: var(--spacing-5);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-primary);
  box-shadow: var(--shadow-sm);
  text-align: center;
}

.app-guard__label {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.app-guard__hint {
  margin: 10px 0 18px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}
</style>
