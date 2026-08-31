<template>
  <section class="monitor-table" aria-label="自选股监控矩阵">
    <div class="monitor-table__toolbar">
      <input v-model="keyword" aria-label="筛选股票" placeholder="筛选名称或代码" />
      <select v-model="status" aria-label="筛选信号状态">
        <option value="all">全部状态</option>
        <option value="attention">关注</option>
        <option value="strong">偏强</option>
        <option value="neutral">中性</option>
        <option value="error">数据不足</option>
      </select>
      <select v-model="movement" aria-label="筛选涨跌方向">
        <option value="all">全部涨跌</option>
        <option value="rising">仅上涨</option>
        <option value="falling">仅下跌</option>
      </select>
      <select v-model="sortBy" aria-label="监控排序">
        <option value="status">按状态</option>
        <option value="change">按涨跌幅</option>
        <option value="relative">按相对上证</option>
        <option value="signals">按信号数量</option>
      </select>
      <label><input v-model="onlyActionable" type="checkbox" /> 仅行动项</label>
      <label><input v-model="onlyCost" type="checkbox" /> 仅有成本</label>
    </div>
    <div class="monitor-table__mobile" role="list" aria-label="移动端自选股监控列表">
      <article v-for="item in items" :key="itemKey(item)" class="monitor-table__mobile-row" :class="{ 'is-selected': item.code === selectedCode }" role="listitem">
        <button type="button" class="monitor-table__mobile-main" :aria-pressed="item.code === selectedCode" @click="emit('select', item.code)">
          <span class="monitor-table__mobile-identity"><strong>{{ item.name }}</strong><small>{{ item.code }}</small></span>
          <span class="monitor-table__mobile-quote"><strong>{{ price(item.quote?.price) }}</strong><span :class="changeClass(item.quote?.change_pct)">{{ change(item.quote?.change_pct) }}</span></span>
          <span class="monitor-table__mobile-return"><small>相对上证</small><span :class="changeClass(item.metrics?.relative_strength_vs_sh_pct)">{{ change(item.metrics?.relative_strength_vs_sh_pct) }}</span></span>
          <span class="monitor-table__mobile-status-block">
            <span class="monitor-table__mobile-status" :data-status="item.status">{{ statusText(item.status) }}</span>
            <small v-if="item.quote?.stale" class="monitor-table__stale">数据已延迟 · {{ formatFetchTime(item.quote?.as_of) }}</small>
            <small v-else-if="item.errors?.length" class="monitor-table__error">数据异常 · {{ item.errors[0] }}</small>
          </span>
        </button>
        <button type="button" class="monitor-table__open" :disabled="retryingCode === item.code" @click="isRetryable(item) ? emit('retry', item.code) : emit('open-stock', item.code)">{{ retryingCode === item.code ? '重试中' : isRetryable(item) ? '重试' : '查看' }}</button>
      </article>
    </div>
    <table class="monitor-table__desktop">
      <thead><tr><th>股票</th><th>现价</th><th>涨跌</th><th>相对上证</th><th>成本收益</th><th>信号</th><th></th></tr></thead>
      <tbody>
        <tr
          v-for="item in items"
          :key="itemKey(item)"
          :class="{ 'is-selected': item.code === selectedCode }"
          :aria-selected="item.code === selectedCode"
          tabindex="0"
          @click="emit('select', item.code)"
          @keydown.enter.prevent="emit('select', item.code)"
        >
          <td><strong>{{ item.name }}</strong><small>{{ item.code }}</small></td>
          <td class="numeric">{{ price(item.quote?.price) }}</td>
          <td class="numeric" :class="changeClass(item.quote?.change_pct)">{{ change(item.quote?.change_pct) }}</td>
          <td class="numeric" :class="changeClass(item.metrics?.relative_strength_vs_sh_pct)">{{ change(item.metrics?.relative_strength_vs_sh_pct) }}</td>
          <td class="numeric" :class="changeClass(item.metrics?.cost_return_pct)">{{ change(item.metrics?.cost_return_pct) }}</td>
          <td>
            <span class="monitor-table__status" :data-status="item.status">{{ statusText(item.status) }}</span>
            <small v-if="item.quote?.stale" class="monitor-table__stale" :title="item.errors?.join('；')">数据已延迟 · {{ formatFetchTime(item.quote?.as_of) }}</small>
            <small v-else-if="item.errors?.length" class="monitor-table__error" :title="item.errors.join('；')">数据异常 · {{ item.errors[0] }}</small>
          </td>
          <td><button type="button" class="monitor-table__open" :disabled="retryingCode === item.code" @click.stop="isRetryable(item) ? emit('retry', item.code) : emit('open-stock', item.code)">{{ retryingCode === item.code ? '重试中' : isRetryable(item) ? '重试' : '查看' }}</button></td>
        </tr>
      </tbody>
    </table>
    <p v-if="!items.length" class="monitor-table__empty">没有匹配的监控股票。</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatChangePct, formatFetchTime, formatPrice } from '@/utils/format'

const props = defineProps({
  items: { type: Array, default: () => [] },
  selectedCode: { type: String, default: '' },
  filters: { type: Object, default: () => ({}) },
  retryingCode: { type: String, default: '' },
})
const emit = defineEmits(['select', 'open-stock', 'retry'])
const keyword = computed({ get: () => props.filters.keyword || '', set: (value) => { props.filters.keyword = value } })
const status = computed({ get: () => props.filters.status || 'all', set: (value) => { props.filters.status = value } })
const movement = computed({ get: () => props.filters.movement || 'all', set: (value) => { props.filters.movement = value } })
const sortBy = computed({ get: () => props.filters.sortBy || 'status', set: (value) => { props.filters.sortBy = value } })
const onlyActionable = computed({ get: () => Boolean(props.filters.onlyActionable), set: (value) => { props.filters.onlyActionable = value } })
const onlyCost = computed({ get: () => Boolean(props.filters.onlyCost), set: (value) => { props.filters.onlyCost = value } })
const statusText = (value) => ({ attention: '关注', strong: '偏强', neutral: '中性', error: '数据不足' })[value] || value
const price = (value) => formatPrice(value)
const change = (value) => formatChangePct(value)
const changeClass = (value) => Number(value) > 0 ? 'text-up' : Number(value) < 0 ? 'text-down' : 'text-neutral'
const isRetryable = (item) => Boolean(item.errors?.length)
const itemKey = (item) => item.watchlist_item_id ?? `${item.code}:${item.group_id ?? ''}`
</script>

<style scoped>
.monitor-table { min-width: 0; background: var(--surface-primary); }
.monitor-table__toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: var(--spacing-2); min-height: 44px; padding: var(--spacing-2) var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.monitor-table__toolbar input:not([type='checkbox']), .monitor-table__toolbar select { min-height: 30px; padding: 0 var(--spacing-2); border: 1px solid var(--border-default); border-radius: var(--radius-xs); background: var(--surface-primary); color: var(--text-primary); }
.monitor-table__toolbar label { color: var(--text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }
table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
th { height: 32px; padding: 0 var(--spacing-3); border-bottom: 1px solid var(--border-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); font-weight: 500; text-align: left; }
td { height: 48px; padding: 4px var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
tbody tr { cursor: pointer; outline: 0; }
tbody tr:hover, tbody tr:focus-visible, tbody tr.is-selected { background: var(--surface-secondary); }
td:first-child { display: grid; gap: 2px; }
td small { color: var(--text-tertiary); font-family: var(--font-family-mono); font-size: var(--font-size-xs); }
.numeric { font-family: var(--font-family-mono); font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.monitor-table__status { color: var(--text-secondary); }
.monitor-table__status[data-status='attention'] { color: var(--text-warning); }
.monitor-table__status[data-status='strong'] { color: var(--text-positive); }
.monitor-table__status[data-status='error'], .monitor-table__mobile-status[data-status='error'] { color: var(--text-negative); }
.monitor-table__mobile { display: none; }
.monitor-table__mobile-main { display: grid; grid-template-columns: minmax(0, 1fr) auto auto auto; align-items: center; gap: var(--spacing-2); min-width: 0; padding: var(--spacing-3); border: 0; background: transparent; color: var(--text-primary); text-align: left; }
.monitor-table__mobile-identity, .monitor-table__mobile-quote, .monitor-table__mobile-return, .monitor-table__mobile-status-block { display: grid; gap: 2px; min-width: 0; }
.monitor-table__mobile-identity strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.monitor-table__mobile-identity small, .monitor-table__mobile-return small { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-table__mobile-quote, .monitor-table__mobile-return { justify-items: end; font-family: var(--font-family-mono); font-size: var(--font-size-xs); font-variant-numeric: tabular-nums; white-space: nowrap; }
.monitor-table__mobile-quote strong { font-size: var(--font-size-sm); }
.monitor-table__mobile-status { color: var(--text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }
.monitor-table__mobile-status-block { justify-items: end; }
.monitor-table__mobile-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; min-height: 64px; border-bottom: 1px solid var(--border-subtle); }
.monitor-table__mobile-row.is-selected { background: var(--surface-secondary); }
.monitor-table__stale, .monitor-table__error { display: block; margin-top: 2px; color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-table__error { color: var(--text-negative); }
.monitor-table__open { padding: 4px 0; border: 0; background: transparent; color: var(--text-link); cursor: pointer; }
.monitor-table__open:disabled { color: var(--text-tertiary); cursor: wait; }
.monitor-table__empty { margin: 0; padding: var(--spacing-5); color: var(--text-tertiary); text-align: center; }
@media (max-width: 767px) { .monitor-table__toolbar { align-items: stretch; flex-wrap: wrap; padding-block: var(--spacing-2); } .monitor-table__toolbar input:not([type='checkbox']) { flex: 1 1 150px; } .monitor-table__desktop { display: none; } .monitor-table__mobile { display: grid; } .monitor-table__open { min-height: 44px; padding: 0 var(--spacing-3); } }
</style>
