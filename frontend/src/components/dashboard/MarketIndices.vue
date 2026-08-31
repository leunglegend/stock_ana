<template>
  <div class="market-indices__grid">
    <article v-for="item in indices" :key="item.key" class="market-indices__item">
      <span class="market-indices__name">{{ item.name }}</span>
      <PriceDisplay
        :price="item.price"
        :change="item.changeAmount"
        :change-percent="item.changePercent"
        size="md"
      />
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import PriceDisplay from '../base/PriceDisplay.vue'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({}),
  },
})

const indices = computed(() => [
  {
    key: 'sh',
    name: '上证指数',
    price: props.summary?.sh_index,
    changeAmount: props.summary?.sh_change_amount,
    changePercent: props.summary?.sh_change_pct,
  },
  {
    key: 'sz',
    name: '深证成指',
    price: props.summary?.sz_index,
    changeAmount: props.summary?.sz_change_amount,
    changePercent: props.summary?.sz_change_pct,
  },
  {
    key: 'cyb',
    name: '创业板指',
    price: props.summary?.cyb_index,
    changeAmount: props.summary?.cyb_change_amount,
    changePercent: props.summary?.cyb_change_pct,
  },
])
</script>

<style scoped>
.market-indices__grid {
  display: grid;
}

.market-indices__grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }

.market-indices__item {
  display: grid;
  gap: var(--spacing-1);
  padding: var(--spacing-3);
  border-left: 1px solid var(--border-subtle);
}

.market-indices__item:first-child {
  border-left: 0;
}

.market-indices__name {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

@media (max-width: 767px) {
  .market-indices__grid {
    grid-template-columns: 1fr;
  }

  .market-indices__item { border-left: 0; border-top: 1px solid var(--border-subtle); }
  .market-indices__item:first-child { border-top: 0; }
}
</style>
