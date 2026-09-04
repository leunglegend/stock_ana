<template>
  <header class="command-bar">
    <div class="command-bar__left">
      <el-button
        v-if="showMenuButton"
        class="command-bar__icon-button"
        text
        :aria-label="menuLabel"
        @click="emit('open-nav')"
      >
        <el-icon><Expand /></el-icon>
      </el-button>
      <span class="command-bar__date">{{ tradingDate }} · 盘后</span>
      <span class="command-bar__status"><i class="command-bar__status-dot" aria-hidden="true"></i>数据正常</span>
    </div>

    <button class="command-bar__search" type="button" @click="emit('open-search')">
      <span class="command-bar__search-label">搜索股票、代码或板块</span>
      <span class="command-bar__search-shortcut">/</span>
    </button>

    <div class="command-bar__right">
      <NotificationBell />
      <SupportButton />
      <CommandBarUtilities />
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Expand } from '@element-plus/icons-vue'

import NotificationBell from '../NotificationBell.vue'
import CommandBarUtilities from './CommandBarUtilities.vue'
import SupportButton from './SupportButton.vue'

const props = defineProps({
  showMenuButton: { type: Boolean, default: false },
})

const emit = defineEmits(['open-search', 'open-nav'])
const menuLabel = computed(() => (props.showMenuButton ? '打开导航菜单' : '导航菜单'))
const currentDate = ref(new Date())
const tradingDate = computed(() => new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  weekday: 'short',
}).format(currentDate.value))
</script>

<style scoped>
.command-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(240px, 320px) minmax(220px, 1fr);
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  min-height: var(--command-bar-height);
  padding: var(--spacing-1) var(--spacing-3);
  background: var(--surface-canvas);
  border-bottom: 1px solid var(--border-subtle);
}

.command-bar__left,
.command-bar__right {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  min-width: 0;
}

.command-bar__search {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  width: 100%;
  min-height: 30px;
  padding: 0 var(--spacing-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  background: var(--surface-canvas);
  color: var(--text-secondary);
  cursor: pointer;
}

.command-bar__search:hover {
  border-color: var(--color-primary-300);
  color: var(--text-primary);
}

.command-bar__search-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.command-bar__search-shortcut {
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  background: var(--surface-panel-strong);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
}

.command-bar__status {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  white-space: nowrap;
}

.command-bar__status-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-down-500);
}

.command-bar__icon-button {
  min-width: 32px;
  min-height: 32px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-secondary);
}

.command-bar__date { color: var(--text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }
.command-bar__right { justify-content: flex-end; }

@media (max-width: 1023px) {
  .command-bar { grid-template-columns: minmax(0, 1fr) minmax(240px, 360px) auto; }
  .command-bar__status { display: none; }
}

@media (max-width: 767px) {
  .command-bar {
    min-height: 48px;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: var(--spacing-2);
    padding-inline: var(--spacing-2);
  }
  .command-bar__left { flex: 1; }
  .command-bar__right { flex: 0 0 auto; }
  .command-bar__date,
  .command-bar__status { display: none; }
  .command-bar__search { min-height: 32px; padding-inline: var(--spacing-2); }
  .command-bar__search-shortcut { display: none; }
  .command-bar__icon-button { width: 44px; min-width: 44px; min-height: 44px; }
}
</style>
