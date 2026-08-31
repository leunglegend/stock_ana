<template>
  <aside class="monitor-inspector" aria-label="股票监控详情">
    <template v-if="item">
      <div class="monitor-inspector__header"><span>当前标的</span><strong>{{ item.name }}</strong><small>{{ item.code }}</small></div>
      <dl>
        <div><dt>最新价</dt><dd>{{ formatPrice(item.quote?.price) }}</dd></div>
        <div><dt>当日涨跌</dt><dd :class="changeClass(item.quote?.change_pct)">{{ formatChangePct(item.quote?.change_pct) }}</dd></div>
        <div><dt>成本收益</dt><dd :class="changeClass(item.metrics?.cost_return_pct)">{{ formatChangePct(item.metrics?.cost_return_pct) }}</dd></div>
      </dl>
      <div v-if="sparklineBars.length" class="monitor-inspector__sparkline-wrap">
        <span class="monitor-inspector__sparkline-label">近 30 日走势</span>
        <div class="monitor-inspector__sparkline" role="img" aria-label="近 30 日收盘走势">
          <span v-for="point in sparklineBars" :key="point.key" :style="{ height: `${point.height}%` }" />
        </div>
      </div>
      <p v-if="item.remark" class="monitor-inspector__remark">备注：{{ item.remark }}</p>
      <p v-if="item.errors?.length" class="monitor-inspector__error" role="alert">数据状态：{{ item.errors.join('；') }}</p>
      <ul class="monitor-inspector__signals"><li v-for="signal in item.signals" :key="`${signal.label}-${signal.detail}`">{{ signal.label }}<small>{{ signal.detail }}</small></li></ul>
      <button type="button" class="monitor-inspector__stock-link" @click="emit('open-stock', item.code)">打开个股详情</button>

      <section class="monitor-inspector__research" aria-label="选中股票按需研究">
        <StatusState v-if="financialState === 'loading'" state="loading" title="正在读取财务字段" :min-height="150" />
        <StatusState v-else-if="financialState === 'error'" state="error" title="财务数据加载失败" description="可进入个股详情重试。" :min-height="150" />
        <StatusState v-else-if="financialState === 'empty'" state="empty" title="暂无财务数据" :min-height="150" />
        <FinancialCard v-else :financial="financial" :loading="false" />
        <AiAdvice :code="item.code" :advice="aiAdvice" :state="aiState" :error-message="aiErrorMessage" @start-analyze="emit('start-analyze')" />
      </section>
    </template>
    <p v-else class="monitor-inspector__empty">选择一只股票查看监控事实。</p>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { formatChangePct, formatPrice } from '@/utils/format'
import AiAdvice from '@/components/AiAdvice.vue'
import FinancialCard from '@/components/FinancialCard.vue'
import StatusState from '@/components/base/StatusState.vue'

const props = defineProps({
  item: { type: Object, default: null },
  financial: { type: Object, default: null },
  financialState: { type: String, default: 'idle' },
  aiAdvice: { type: String, default: '' },
  aiState: { type: String, default: 'idle' },
  aiErrorMessage: { type: String, default: '' },
})
const emit = defineEmits(['open-stock', 'start-analyze'])
const changeClass = (value) => Number(value) > 0 ? 'text-up' : Number(value) < 0 ? 'text-down' : 'text-neutral'
const sparklineBars = computed(() => {
  const values = (props.item?.sparkline || []).map((point) => Number(point.close)).filter(Number.isFinite)
  if (!values.length) return []
  const min = Math.min(...values)
  const range = Math.max(...values) - min || 1
  return values.map((value, index) => ({ key: `${index}-${value}`, height: Math.max(8, ((value - min) / range) * 92) }))
})
</script>

<style scoped>
.monitor-inspector { padding: var(--spacing-3); border-left: 1px solid var(--border-subtle); background: var(--surface-primary); }
.monitor-inspector__header { display: flex; align-items: baseline; flex-wrap: wrap; gap: var(--spacing-2); padding-bottom: var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.monitor-inspector__header span, .monitor-inspector__header small, dt, .monitor-inspector__empty { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-inspector__header strong { font-size: var(--font-size-lg); }
dl { display: grid; gap: var(--spacing-2); margin: var(--spacing-3) 0; }
dl div { display: flex; align-items: baseline; justify-content: space-between; gap: var(--spacing-3); }
dt, dd { margin: 0; }
dd { font-family: var(--font-family-mono); font-variant-numeric: tabular-nums; }
.monitor-inspector__remark { margin: 0 0 var(--spacing-3); color: var(--text-secondary); font-size: var(--font-size-xs); }
.monitor-inspector__error { margin: 0 0 var(--spacing-3); color: var(--text-negative); font-size: var(--font-size-xs); line-height: var(--line-height-normal); }
.monitor-inspector__sparkline-wrap { display: grid; gap: var(--spacing-2); padding: var(--spacing-3) 0; border-bottom: 1px solid var(--border-subtle); }
.monitor-inspector__sparkline-label { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-inspector__sparkline { display: flex; align-items: end; gap: 2px; height: 44px; padding: 4px 0; border-bottom: 1px solid var(--border-default); }
.monitor-inspector__sparkline span { flex: 1; min-width: 2px; background: var(--color-primary-400); }
.monitor-inspector__signals { display: grid; gap: var(--spacing-2); padding: 0 0 var(--spacing-3); margin: 0; border-bottom: 1px solid var(--border-subtle); list-style: none; }
.monitor-inspector__signals li { display: grid; gap: 2px; color: var(--text-primary); font-size: var(--font-size-sm); }
.monitor-inspector__signals small { color: var(--text-tertiary); }
.monitor-inspector__stock-link { margin-top: var(--spacing-3); padding: 0; border: 0; background: transparent; color: var(--text-link); cursor: pointer; }
.monitor-inspector__research { margin-top: var(--spacing-4); border-top: 1px solid var(--border-subtle); }
.monitor-inspector__research :deep(.financial-card), .monitor-inspector__research :deep(.ai-advice-card) { padding-inline: 0; }
.monitor-inspector__empty { margin: 0; line-height: 1.6; }
@media (max-width: 1023px) { .monitor-inspector { border-left: 0; border-top: 1px solid var(--border-subtle); } }
</style>
