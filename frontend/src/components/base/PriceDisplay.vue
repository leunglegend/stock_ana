<template>
  <div class="price-display" :class="`price-display--${size}`">
    <span class="price-display__price" :class="colorClass">
      {{ formattedPrice }}
    </span>

    <span v-if="showChange" class="price-display__change" :class="colorClass">
      <span class="price-display__change-amount">{{ changeWithSign }}</span>
      <span v-if="showPercent" class="price-display__change-percent">
        ({{ percentWithSign }})
      </span>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  price: {
    type: Number,
    default: null
  },
  change: {
    type: Number,
    default: undefined
  },
  changePercent: {
    type: Number,
    default: undefined
  },
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val)
  }
})

const showChange = computed(() => props.change !== undefined && props.change !== null)
const showPercent = computed(() => props.changePercent !== undefined && props.changePercent !== null)

const movement = computed(() => {
  const value = props.change
  if (value == null) return 'flat'
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'flat'
})

const colorClass = computed(() => `price-display--${movement.value}`)

const formattedPrice = computed(() => {
  if (props.price === undefined || props.price === null) return '--'
  return props.price.toFixed(2)
})

const changeWithSign = computed(() => {
  const val = props.change
  if (val === undefined || val === null) return '--'
  if (val > 0) return `+${val.toFixed(2)}`
  return val.toFixed(2)
})

const percentWithSign = computed(() => {
  const val = props.changePercent
  if (val === undefined || val === null) return '--'
  if (val > 0) return `+${val.toFixed(2)}%`
  return `${val.toFixed(2)}%`
})
</script>

<style scoped>
.price-display {
  display: inline-flex;
  align-items: baseline;
  gap: var(--spacing-2);
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.price-display--up {
  color: var(--text-positive);
}

.price-display--down {
  color: var(--text-negative);
}

.price-display--flat {
  color: var(--text-secondary);
}

.price-display__price {
  font-family: var(--font-family-mono);
  font-weight: 600;
}

.price-display__change {
  display: inline-flex;
  align-items: baseline;
  gap: var(--spacing-1);
  font-weight: 500;
}

.price-display--sm .price-display__price {
  font-size: var(--font-size-xl);
}

.price-display--sm .price-display__change {
  font-size: var(--font-size-xs);
}

.price-display--md .price-display__price {
  font-size: var(--font-size-2xl);
}

.price-display--md .price-display__change {
  font-size: var(--font-size-sm);
}

.price-display--lg .price-display__price {
  font-size: var(--font-size-4xl);
}

.price-display--lg .price-display__change {
  font-size: var(--font-size-base);
}
</style>
