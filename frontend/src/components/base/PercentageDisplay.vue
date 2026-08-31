<template>
  <span
    class="percentage-display"
    :class="[`percentage-display--${size}`, `percentage-display--${movement}`]"
  >
    {{ displayValue }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

import { safeNumber } from '../../utils/format'

const props = defineProps({
  value: {
    type: [Number, String],
    default: null,
  },
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val),
  },
})

const numericValue = computed(() => safeNumber(props.value))

const movement = computed(() => {
  if (numericValue.value == null) return 'flat'
  if (numericValue.value > 0) return 'up'
  if (numericValue.value < 0) return 'down'
  return 'flat'
})

const displayValue = computed(() => {
  if (numericValue.value == null) return '--'
  const sign = numericValue.value > 0 ? '+' : ''
  return `${sign}${numericValue.value.toFixed(2)}%`
})
</script>

<style scoped>
.percentage-display {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-family-mono);
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
  font-weight: 700;
  white-space: nowrap;
}

.percentage-display--up {
  color: var(--text-positive);
}

.percentage-display--down {
  color: var(--text-negative);
}

.percentage-display--flat {
  color: var(--text-secondary);
}

.percentage-display--sm {
  font-size: var(--font-size-base);
}

.percentage-display--md {
  font-size: var(--font-size-2xl);
}

.percentage-display--lg {
  font-size: var(--font-size-4xl);
}
</style>
