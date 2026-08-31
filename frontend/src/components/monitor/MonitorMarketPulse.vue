<template>
  <section class="monitor-market" aria-label="市场脉搏">
    <div class="monitor-market__headline"><span>市场环境</span><strong>{{ market?.environment || '未知' }}</strong></div>
    <div class="monitor-market__grid">
      <div v-for="item in metrics" :key="item.label" class="monitor-market__metric"><span>{{ item.label }}</span><strong>{{ item.value }}</strong><small v-if="item.change">{{ item.change }}</small></div>
    </div>
  </section>
</template>
<script setup>
import { computed } from 'vue'
import { formatChangePct, formatPrice, formatYi } from '@/utils/format'
const props = defineProps({ market: { type: Object, default: null }, summary: { type: Object, default: () => ({}) } })
const metrics = computed(() => {
  const summary = props.market?.summary || props.summary || {}
  return [
    { label: '上证指数', value: formatPrice(summary.sh_index), change: formatChangePct(summary.sh_change_pct) },
    { label: '深证成指', value: formatPrice(summary.sz_index), change: formatChangePct(summary.sz_change_pct) },
    { label: '创业板指', value: formatPrice(summary.cyb_index), change: formatChangePct(summary.cyb_change_pct) },
    { label: '上涨 / 下跌', value: `${summary.rise_count ?? '--'} / ${summary.fall_count ?? '--'}` },
    { label: '涨停 / 跌停', value: `${summary.limit_up_count ?? '--'} / ${summary.limit_down_count ?? '--'}` },
    { label: '两市成交额', value: formatYi(summary.total_amount) },
  ]
})
</script>
<style scoped>
.monitor-market { border-bottom: 1px solid var(--border-subtle); }
.monitor-market__headline { display: flex; align-items: baseline; justify-content: space-between; padding: var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.monitor-market__headline span, .monitor-market__metric span, .monitor-market__metric small { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-market__headline strong { color: var(--text-primary); font-size: var(--font-size-lg); }
.monitor-market__grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); }
.monitor-market__metric { display: grid; gap: 3px; min-height: 70px; padding: var(--spacing-3); border-right: 1px solid var(--border-subtle); }
.monitor-market__metric:last-child { border-right: 0; }
.monitor-market__metric strong { color: var(--text-primary); font-family: var(--font-family-mono); font-size: var(--font-size-base); }
.monitor-market__metric small { font-family: var(--font-family-mono); }
@media (max-width: 767px) { .monitor-market__grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .monitor-market__metric:nth-child(2n) { border-right: 0; } .monitor-market__metric:nth-child(n + 3) { border-top: 1px solid var(--border-subtle); } }
</style>
