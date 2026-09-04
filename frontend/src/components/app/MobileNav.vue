<template>
  <nav
    class="mobile-nav"
    :style="{ '--mobile-nav-columns': String(Math.max(props.items.length, 1)) }"
    aria-label="移动主导航"
  >
    <RouterLink
      v-for="item in items"
      :key="item.path"
      :to="item.path"
      class="mobile-nav__item"
      :class="{ 'is-active': isActive(item) }"
    >
      <span>{{ item.compactTitle || item.title }}</span>
    </RouterLink>
  </nav>
</template>

<script setup>
import { RouterLink, useRoute } from 'vue-router'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

const route = useRoute()

function isActive(item) {
  if (item.id === 'reports') return route.path === '/reports'
  if (item.id === 'report-detail') return route.path.startsWith('/reports/')
  if (item.id === 'stock') return route.path.startsWith('/stock/')
  if (item.id === 'us') return route.path === '/us' || route.path.startsWith('/us/')
  return route.path === item.path
}
</script>

<style scoped>
.mobile-nav {
  display: flex;
  min-width: 0;
  min-height: 42px;
  overflow-x: auto;
  background: var(--surface-canvas);
  border-bottom: 1px solid var(--border-subtle);
  scrollbar-width: none;
}

.mobile-nav__item {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  padding: 0 var(--spacing-3);
  border-bottom: 2px solid transparent;
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  white-space: nowrap;
}

.mobile-nav__item.is-active {
  color: var(--text-primary);
  border-bottom-color: var(--color-primary-500);
  font-weight: 600;
}
</style>
