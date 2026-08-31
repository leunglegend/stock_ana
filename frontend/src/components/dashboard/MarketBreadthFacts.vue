<template>
  <SectionPanel class="market-breadth-facts" variant="flush">
    <template #header><h3 class="market-breadth-facts__title">市场宽度</h3></template>
    <div class="market-breadth-facts__grid">
      <div v-for="fact in facts" :key="fact.label" class="market-breadth-facts__item">
        <span>{{ fact.label }}</span><strong>{{ fact.value }}</strong>
      </div>
    </div>
  </SectionPanel>
</template>
<script setup>
import { computed } from 'vue'
import SectionPanel from '../base/SectionPanel.vue'
import { formatPercent, formatThousands } from '../../utils/format'

const props = defineProps({ summary: { type: Object, default: () => ({}) } })
const facts = computed(() => [
  { label: '上涨家数', value: formatThousands(props.summary.rise_count) },
  { label: '下跌家数', value: formatThousands(props.summary.fall_count) },
  { label: '涨停家数', value: formatThousands(props.summary.limit_up_count) },
  { label: '跌停家数', value: formatThousands(props.summary.limit_down_count) },
  { label: '强势板块 (>=3%)', value: formatThousands(props.summary.strong_board_count) },
  { label: '板块涨跌中位数', value: formatPercent(props.summary.median_board_change, 2, false) },
])
</script>
<style scoped>
.market-breadth-facts__title{margin:0;color:var(--text-primary);font-size:var(--font-size-base)}
.market-breadth-facts__grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}
.market-breadth-facts__item{display:grid;gap:2px;min-width:0;padding:var(--spacing-2) var(--spacing-3);border-right:1px solid var(--border-subtle);border-bottom:1px solid var(--border-subtle);color:var(--text-tertiary);font-size:var(--font-size-xs)}
.market-breadth-facts__item:nth-child(2n){border-right:0}.market-breadth-facts__item:nth-last-child(-n+2){border-bottom:0}
.market-breadth-facts__item strong{color:var(--text-primary);font-family:var(--font-family-mono);font-size:var(--font-size-sm)}
</style>
