<template>
  <span class="tag-badge" :class="[`tag-badge--${type}`, `tag-badge--${size}`]">
    <slot>{{ text }}</slot>
  </span>
</template>

<script setup>
const props = defineProps({
  text: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'default',
    validator: (val) =>
      ['primary', 'success', 'warning', 'danger', 'info', 'default', 'up', 'down'].includes(val)
  },
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md'].includes(val)
  }
})
</script>

<style scoped>
.tag-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  transition:
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    color var(--transition-fast);
}

.tag-badge--sm {
  padding: 3px 8px;
  font-size: 11px;
}

.tag-badge--md {
  padding: 4px 10px;
  font-size: 12px;
}

.tag-badge--primary {
  background: var(--color-primary-50);
  border-color: var(--state-selected);
  color: var(--color-primary-700);
}

.tag-badge--success {
  background: var(--surface-negative);
  border-color: var(--border-negative);
  color: var(--text-negative);
}

.tag-badge--warning {
  background: var(--surface-warning);
  border-color: var(--border-ai);
  color: var(--text-warning);
}

.tag-badge--danger {
  background: var(--surface-positive);
  border-color: var(--border-positive);
  color: var(--text-positive);
}

.tag-badge--info {
  background: var(--surface-info);
  border-color: var(--state-selected);
  color: var(--color-info-600);
}

.tag-badge--default {
  background: var(--surface-panel-strong);
  border-color: var(--border-subtle);
  color: var(--text-secondary);
}

.tag-badge--up {
  background: var(--surface-positive);
  border-color: var(--border-positive);
  color: var(--text-positive);
}

.tag-badge--down {
  background: var(--surface-negative);
  border-color: var(--border-negative);
  color: var(--text-negative);
}
</style>
