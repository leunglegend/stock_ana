<template>
  <div class="metric-cell" :class="`metric-cell--${tone}`">
    <span class="metric-cell__label">{{ label }}</span>
    <div class="metric-cell__value-row">
      <span class="metric-cell__value">{{ displayValue }}</span>
      <span v-if="unit && !isMissing" class="metric-cell__unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { isDisplayValueMissing, safeNumber } from '../../utils/format.js'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: [Number, String],
    default: null,
  },
  unit: {
    type: String,
    default: '',
  },
  tone: {
    type: String,
    default: 'neutral',
    validator: (value) => ['positive', 'negative', 'neutral'].includes(value),
  },
  decimals: {
    type: Number,
    default: null,
  },
  placeholder: {
    type: String,
    default: '--',
  },
})

const normalizedNumber = computed(() => safeNumber(props.value))
const isMissing = computed(() => isDisplayValueMissing(props.value))

const displayValue = computed(() => {
  if (isMissing.value) return props.placeholder
  if (normalizedNumber.value == null) return String(props.value)
  if (props.decimals == null) return `${normalizedNumber.value}`
  return normalizedNumber.value.toFixed(props.decimals)
})
</script>

<style scoped>
.metric-cell {
  display: grid;
  gap: var(--spacing-2);
}

.metric-cell__label {
  color: var(--color-gray-500);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

.metric-cell__value-row {
  display: inline-flex;
  align-items: baseline;
  gap: var(--spacing-1);
  min-width: 0;
}

.metric-cell__value,
.metric-cell__unit {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.metric-cell__value {
  color: var(--text-primary);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-3xl);
  font-weight: 700;
  line-height: var(--line-height-tight);
}

.metric-cell__unit {
  color: var(--color-gray-500);
  font-size: var(--font-size-sm);
}

.metric-cell--positive .metric-cell__value {
  color: var(--text-positive);
}

.metric-cell--negative .metric-cell__value {
  color: var(--text-negative);
}

.metric-cell--neutral .metric-cell__value {
  color: var(--text-primary);
}
</style>
