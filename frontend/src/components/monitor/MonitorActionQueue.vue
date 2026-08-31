<template>
  <aside class="monitor-queue" aria-label="待处理行动队列">
    <div class="monitor-queue__header">
      <h2>行动队列</h2>
      <span>{{ items.length }} 项</span>
    </div>
    <p v-if="!items.length" class="monitor-queue__empty">暂无需要优先处理的信号。</p>
    <ul v-else class="monitor-queue__list">
      <li v-for="item in items" :key="item.code">
        <button type="button" class="monitor-queue__item" @click="emit('open-stock', item.code)">
          <span class="monitor-queue__item-main">
            <strong>{{ item.name }}</strong>
            <small>{{ item.code }}</small>
          </span>
          <span class="monitor-queue__priority" :data-priority="item.priority">{{ priorityText(item.priority) }}</span>
          <span class="monitor-queue__reason">{{ item.reasons?.[0] || '存在待确认信号' }}</span>
        </button>
      </li>
    </ul>
  </aside>
</template>

<script setup>
defineProps({ items: { type: Array, default: () => [] } })
const emit = defineEmits(['open-stock'])
const priorityText = (value) => value === 'high' ? '优先' : '关注'
</script>

<style scoped>
.monitor-queue { border-left: 1px solid var(--border-subtle); background: var(--surface-primary); }
.monitor-queue__header { display: flex; align-items: baseline; justify-content: space-between; padding: var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.monitor-queue h2 { margin: 0; font-size: var(--font-size-base); }
.monitor-queue__header span, .monitor-queue__empty { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-queue__empty { margin: 0; padding: var(--spacing-4); }
.monitor-queue__list { display: grid; gap: 0; padding: 0; margin: 0; list-style: none; }
.monitor-queue__item { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px var(--spacing-2); width: 100%; padding: var(--spacing-3); border: 0; border-bottom: 1px solid var(--border-subtle); background: transparent; color: var(--text-primary); text-align: left; cursor: pointer; }
.monitor-queue__item:hover { background: var(--surface-secondary); }
.monitor-queue__item-main { display: inline-flex; gap: var(--spacing-2); min-width: 0; }
.monitor-queue__item-main strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.monitor-queue__item-main small, .monitor-queue__reason { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-queue__priority { color: var(--text-warning); font-size: var(--font-size-xs); }
.monitor-queue__priority[data-priority='high'] { color: var(--text-negative); }
.monitor-queue__reason { grid-column: 1 / -1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 1023px) { .monitor-queue { border-left: 0; border-top: 1px solid var(--border-subtle); } }
</style>
