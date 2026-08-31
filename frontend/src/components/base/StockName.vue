<template>
  <div class="stock-name" :class="`stock-name--${size}`">
    <span class="stock-name__text">{{ name }}</span>
    <span class="stock-name__code">{{ code }}</span>
  </div>
</template>

<script setup>
const props = defineProps({
  name: {
    type: String,
    required: true
  },
  code: {
    type: String,
    required: true
  },
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val)
  }
})
</script>

<style scoped>
.stock-name {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--spacing-2);
  font-feature-settings: 'tnum';
  max-width: 100%;
}

.stock-name__text {
  font-weight: 600;
  color: var(--text-primary);
  overflow-wrap: anywhere;
}

.stock-name__code {
  font-family: var(--font-family-mono);
  color: var(--text-tertiary);
  white-space: nowrap;
}

.stock-name--sm .stock-name__text {
  font-size: var(--font-size-sm);
}

.stock-name--sm .stock-name__code {
  font-size: 11px;
}

.stock-name--md .stock-name__text {
  font-size: var(--font-size-base);
}

.stock-name--md .stock-name__code {
  font-size: var(--font-size-xs);
}

.stock-name--lg .stock-name__text {
  font-size: var(--font-size-lg);
}

.stock-name--lg .stock-name__code {
  font-size: var(--font-size-sm);
}
</style>
