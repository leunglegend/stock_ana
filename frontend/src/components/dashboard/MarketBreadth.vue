<template>
  <div class="market-breadth">
    <div class="market-breadth__grid">
      <MetricCell label="涨跌家数" :value="marketBreadthLabel" />
      <MetricCell label="涨停 / 跌停" :value="limitLabel" />
      <MetricCell label="两市成交额" :value="amountLabel" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import MetricCell from '../base/MetricCell.vue'
import { formatAmount, formatThousands } from '../../utils/format'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({}),
  },
})

const marketBreadthLabel = computed(() => `${formatThousands(props.summary?.rise_count)} / ${formatThousands(props.summary?.fall_count)}`)
const limitLabel = computed(() => `${formatThousands(props.summary?.limit_up_count)} / ${formatThousands(props.summary?.limit_down_count)}`)
const amountLabel = computed(() => formatAmount(props.summary?.total_amount))
</script>

<style scoped>
.market-breadth { min-width: 0; }
.market-breadth__grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }

@media (max-width: 767px) {
  .market-breadth__grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
