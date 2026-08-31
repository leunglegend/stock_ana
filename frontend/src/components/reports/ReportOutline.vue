<template>
  <aside class="outline">
    <nav aria-label="报告目录">
      <strong>报告目录</strong>
      <a v-for="item in items" :key="item.id" :href="`#${item.id}`">{{ item.label }}</a>
    </nav>
  </aside>
</template>

<script setup>
defineProps({ items: { type: Array, default: () => [] } })
</script>

<style scoped>
.outline { position: sticky; top: 84px; width: 180px; align-self: start; border-right: 1px solid var(--border-subtle); }
.outline nav { display: grid; padding: var(--spacing-3) 0; }
.outline strong { padding: 0 var(--spacing-3) var(--spacing-2); color: var(--text-secondary); font-size: var(--font-size-xs); font-weight: 500; }
.outline a { min-height: 36px; display: flex; align-items: center; padding: 0 var(--spacing-3); border-left: 2px solid transparent; color: var(--text-secondary); font-size: var(--font-size-sm); text-decoration: none; }
.outline a:hover, .outline a:focus-visible { border-left-color: var(--color-primary); background: var(--surface-secondary); color: var(--text-primary); outline: 0; }
@media (max-width: 900px) { .outline { position: static; width: auto; border-right: 0; border-bottom: 1px solid var(--border-subtle); } .outline nav { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; } .outline strong { grid-column: 1 / -1; } }
</style>
