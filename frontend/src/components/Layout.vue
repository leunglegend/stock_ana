<template>
  <div class="app-shell">
    <DesktopSidebar v-if="isDesktop" :items="navItems" />

    <el-drawer
      v-model="drawerVisible"
      class="app-shell__drawer"
      direction="ltr"
      :with-header="false"
      size="280px"
    >
      <DesktopSidebar embedded :items="navItems" @navigate="drawerVisible = false" />
    </el-drawer>

    <div class="app-shell__main">
      <CommandBar
        :show-menu-button="!isDesktop"
        @open-nav="drawerVisible = true"
        @open-search="searchVisible = true"
      />
      <MobileNav v-if="isMobile" :items="navItems" />

      <main class="app-shell__content">
        <RouterView v-slot="{ Component }">
          <transition name="shell-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>
    </div>

    <GlobalSearch v-model="searchVisible" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterView } from 'vue-router'

import DesktopSidebar from './app/DesktopSidebar.vue'
import CommandBar from './app/CommandBar.vue'
import MobileNav from './app/MobileNav.vue'
import GlobalSearch from './GlobalSearch.vue'
import { useResponsive } from '@/composables/useResponsive'

const drawerVisible = ref(false)
const searchVisible = ref(false)
const { isDesktop, isMobile } = useResponsive()

const navBlueprint = [
  { path: '/', title: '市场', icon: 'Odometer' },
  { path: '/monitor', title: '盘中监控', compactTitle: '监控', icon: 'Monitor' },
  { path: '/board', title: '板块', icon: 'DataAnalysis' },
  { path: '/radar', title: '雷达', icon: 'TrendCharts' },
  { path: '/watchlist', title: '自选', icon: 'Star' },
  { path: '/stock/600519', title: '个股', icon: 'Money' },
  { path: '/search', title: '搜索', icon: 'Search' },
  { path: '/reports', title: '报告', icon: 'Document' },
  { path: '/reports/latest', title: '报告详情', compactTitle: '详情', icon: 'Reading' },
]

function resolveNavId(path) {
  if (path === '/reports/latest') return 'report-detail'
  if (path === '/reports') return 'reports'
  if (path === '/stock/600519') return 'stock'
  if (path === '/watchlist') return 'watchlist'
  if (path === '/search') return 'search'
  if (path === '/board') return 'board'
  if (path === '/radar') return 'radar'
  if (path === '/monitor') return 'monitor'
  return 'market'
}

const navItems = navBlueprint.map((item) => ({
  ...item,
  id: resolveNavId(item.path),
}))
</script>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  min-height: 100dvh;
  background: transparent;
}

.app-shell__main {
  flex: 1;
  min-width: 0;
  margin-left: 168px;
}

.app-shell__content {
  min-height: calc(100dvh - var(--command-bar-height));
  padding: 0 var(--spacing-4) var(--spacing-4);
}

.shell-fade-enter-active,
.shell-fade-leave-active {
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast);
}

.shell-fade-enter-from,
.shell-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@media (min-width: 768px) and (max-width: 1023px) {
  .app-shell__main {
    padding: 0 var(--spacing-3) var(--spacing-3);
  }

  .app-shell__content {
    min-height: calc(100dvh - var(--command-bar-height));
    padding: 0;
  }
}

@media (min-width: 1024px) and (max-width: 1279px) {
  .app-shell__main { margin-left: 64px; }
}

@media (max-width: 767px) {
  .app-shell__main {
    margin-left: 0;
    padding: 0;
  }

  .app-shell__content {
    min-height: auto;
    padding: 0 var(--spacing-2) var(--spacing-4);
  }
}
</style>
