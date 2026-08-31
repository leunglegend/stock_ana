<template>
  <aside class="desktop-sidebar" :class="{ 'desktop-sidebar--embedded': embedded }">
    <div class="desktop-sidebar__brand">
      <div class="desktop-sidebar__logo" aria-hidden="true">XG</div>
      <div class="desktop-sidebar__brand-copy">
        <p class="desktop-sidebar__title">析股研究台</p>
      </div>
    </div>

    <p class="desktop-sidebar__label">研究工作区</p>
    <nav class="desktop-sidebar__nav" aria-label="主导航">
      <RouterLink
        v-for="item in items"
        :key="item.path"
        :to="item.path"
        class="desktop-sidebar__link"
        :class="{ 'is-active': isActive(item) }"
        :title="item.title"
        @click="emit('navigate')"
      >
        <el-icon :size="18">
          <component :is="item.icon" />
        </el-icon>
        <span>{{ item.title }}</span>
      </RouterLink>
    </nav>

    <div class="desktop-sidebar__spacer"></div>
    <div class="desktop-sidebar__status">
      <strong>交易日 · 盘后</strong>
      <span>{{ localTime }}</span>
      <span>行情状态：数据正常</span>
    </div>
  </aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  embedded: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['navigate'])
const route = useRoute()
const now = ref(new Date())
let clockTimer = null

const localTime = computed(() => new Intl.DateTimeFormat('zh-CN', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
}).format(now.value))

function isActive(item) {
  if (item.id === 'reports') return route.path === '/reports'
  if (item.id === 'report-detail') return route.path.startsWith('/reports/')
  if (item.id === 'stock') return route.path.startsWith('/stock/')
  return route.path === item.path
}

onMounted(() => {
  clockTimer = window.setInterval(() => { now.value = new Date() }, 1000)
})

onBeforeUnmount(() => window.clearInterval(clockTimer))
</script>

<style scoped>
.desktop-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  z-index: var(--z-sticky);
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 168px;
  height: 100dvh;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  background: var(--surface-sidebar);
  border-right: 1px solid var(--surface-sidebar-hover);
}

.desktop-sidebar--embedded {
  position: static;
  z-index: auto;
  min-height: auto;
  width: 100%;
  height: auto;
  padding: var(--spacing-3);
  overflow: visible;
  border-right: 0;
}

.desktop-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 48px;
  padding: 0 var(--spacing-3);
  border-bottom: 1px solid var(--surface-sidebar-hover);
}

.desktop-sidebar__logo {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border: 1px solid var(--text-sidebar-muted);
  color: var(--text-sidebar);
  font-family: var(--font-family-mono);
  font-size: 11px;
  font-weight: 600;
}

.desktop-sidebar__title {
  margin: 0;
  color: var(--text-sidebar);
  font-size: 15px;
  font-weight: 650;
}

.desktop-sidebar__label {
  margin: var(--spacing-3) var(--spacing-3) var(--spacing-1);
  color: var(--text-sidebar-muted);
  font-size: 10px;
}

.desktop-sidebar__nav {
  display: grid;
  gap: 2px;
  padding: 0 var(--spacing-2);
}

.desktop-sidebar__link {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 36px;
  padding: 0 var(--spacing-2);
  border: 0;
  border-left: 2px solid transparent;
  border-radius: 0;
  color: var(--text-sidebar-muted);
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast),
    border-color var(--transition-fast);
}

.desktop-sidebar__link:hover {
  background: var(--surface-sidebar-hover);
  color: var(--text-sidebar);
}

.desktop-sidebar__link.is-active {
  background: var(--surface-sidebar-active);
  border-left-color: var(--color-primary-300);
  color: var(--text-sidebar);
}

.desktop-sidebar__spacer { flex: 1; }

.desktop-sidebar__status {
  display: grid;
  gap: 3px;
  margin: 0 var(--spacing-3) var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--surface-sidebar-hover);
  color: var(--text-sidebar-muted);
  font-size: 11px;
  line-height: 1.4;
}

.desktop-sidebar__status strong { color: var(--text-sidebar); font-weight: 500; }

@media (min-width: 1024px) and (max-width: 1279px) {
  .desktop-sidebar:not(.desktop-sidebar--embedded) {
    align-items: center;
    width: 64px;
    padding: var(--spacing-2);
  }

  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__brand {
    justify-content: center;
  }

  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__brand-copy,
  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__link span {
    display: none;
  }

  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__label,
  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__status {
    display: none;
  }

  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__nav {
    width: 100%;
  }

  .desktop-sidebar:not(.desktop-sidebar--embedded) .desktop-sidebar__link {
    justify-content: center;
    padding-inline: 0;
  }
}
</style>
