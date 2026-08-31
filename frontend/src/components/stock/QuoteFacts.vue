<template>
  <section class="quote-facts">
    <header class="quote-facts__header">
      <h2 class="quote-facts__title">行情事实</h2>
      <span class="quote-facts__date">当日</span>
    </header>

    <div class="quote-facts__grid">
      <MetricCell label="今开" :value="stock?.open" :decimals="2" />
      <MetricCell label="昨收" :value="stock?.pre_close" :decimals="2" />
      <MetricCell label="最高" :value="stock?.high" :decimals="2" tone="positive" />
      <MetricCell label="最低" :value="stock?.low" :decimals="2" tone="negative" />
      <MetricCell label="成交量" :value="formatVolume(stock?.volume)" />
      <MetricCell label="成交额" :value="formatAmount(stock?.amount)" />
    </div>
  </section>
</template>

<script setup>
import MetricCell from '../base/MetricCell.vue'
import { formatAmount, formatVolume } from '../../utils/format'

defineProps({
  stock: {
    type: Object,
    default: null,
  },
})
</script>

<style scoped>
.quote-facts__header { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-3); min-height: var(--table-head-height); padding: var(--spacing-2) var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.quote-facts__title {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}
.quote-facts__date { color: var(--text-tertiary); font-size: var(--font-size-sm); }

.quote-facts__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-2);
  padding: var(--spacing-3);
}

@media (max-width: 767px) {
  .quote-facts__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
