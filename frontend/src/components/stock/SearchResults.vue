<template>
  <section class="search-results" :aria-label="title">
    <StatusState
      v-if="state === 'idle'"
      state="empty"
      title="输入关键词开始搜索"
      :min-height="260"
    />

    <StatusState
      v-else-if="state === 'loading' && items.length === 0"
      state="loading"
      title="正在搜索股票"
      :min-height="260"
    />

    <StatusState
      v-else-if="state === 'error'"
      state="error"
      title="搜索失败"
      description="暂时无法获取搜索结果，请重试。"
      :min-height="260"
      @retry="$emit('retry-search')"
    />

    <StatusState
      v-else-if="state === 'empty'"
      state="empty"
      title="没有找到匹配股票"
      :min-height="260"
    />

    <div v-else class="search-results__table-wrap">
      <table class="search-results__table">
        <thead><tr><th>股票</th><th class="search-results__numeric">最新价</th><th class="search-results__numeric">涨跌幅</th><th class="search-results__status">行情状态</th><th class="search-results__actions-head">操作</th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.code" class="search-results__row">
            <td><StockName :name="item.name" :code="item.code" /></td>
            <td class="search-results__numeric">
              <span v-if="item.quoteStatus === 'success'" class="search-results__number">{{ formatPrice(item.price) }}</span>
              <span v-else class="search-results__pending">--</span>
            </td>
            <td class="search-results__numeric">
              <span v-if="item.quoteStatus === 'success'" class="search-results__number" :class="movementClass(item.changePercent)">{{ formatPercent(item.changePercent) }}</span>
              <span v-else class="search-results__pending">--</span>
            </td>
            <td class="search-results__status">
              <span v-if="item.quoteStatus === 'loading'" class="search-results__pending">行情加载中</span>
              <div v-else-if="item.quoteStatus === 'error'" class="search-results__error">
                <span>行情失败</span><el-button link type="primary" @click="$emit('retry-quote', item.code)">重试</el-button>
              </div>
              <span v-else-if="item.quoteStatus === 'success'" class="search-results__pending">已更新</span>
              <span v-else class="search-results__pending">基础命中</span>
            </td>
            <td class="search-results__actions">
              <el-button link type="primary" @click="$emit('open-stock', item.code)">详情</el-button>
              <el-button link type="primary" @click="$emit('add-stock', item)">加自选</el-button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import StatusState from '../base/StatusState.vue'
import StockName from '../base/StockName.vue'
import { formatPercent, formatPrice } from '@/utils/format'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  state: {
    type: String,
    default: 'idle',
  },
  title: {
    type: String,
    default: '搜索结果',
  },
})

defineEmits(['open-stock', 'add-stock', 'retry-quote', 'retry-search'])

function movementClass(value) {
  if (value > 0) return 'text-up'
  if (value < 0) return 'text-down'
  return ''
}
</script>

<style scoped>
.search-results { min-width: 0; background: var(--surface-primary); }
.search-results__table-wrap { min-width: 0; overflow-x: auto; }
.search-results__table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.search-results__table th { height: 32px; padding: 0 var(--spacing-2); border-bottom: 1px solid var(--border-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); font-weight: 500; text-align: left; }
.search-results__row { min-height: 44px; border-bottom: 1px solid var(--border-subtle); }
.search-results__row:hover { background: var(--surface-secondary); }
.search-results__row td { height: 44px; padding: 0 var(--spacing-2); vertical-align: middle; }
.search-results__numeric { color: var(--text-primary); font-family: var(--font-family-mono); font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.search-results__number { font-variant-numeric: tabular-nums; }
.search-results__status { width: 110px; }
.search-results__actions, .search-results__actions-head { width: 112px; text-align: right; white-space: nowrap; }
.search-results__pending { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.search-results__error { display: inline-flex; align-items: center; gap: 4px; color: var(--text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }

@media (max-width: 767px) {
  .search-results__table, .search-results__table tbody { display: block; }
  .search-results__table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  .search-results__row { display: grid; grid-template-columns: minmax(0, 1fr) auto; min-width: 0; padding: 6px var(--spacing-3); }
  .search-results__row td { display: flex; align-items: center; min-width: 0; height: auto; padding: 0; }
  .search-results__row td:first-child { grid-column: 1; }
  .search-results__numeric { grid-row: 2; justify-content: flex-start; margin-top: 2px; }
  .search-results__numeric + .search-results__numeric { margin-left: var(--spacing-3); }
  .search-results__status { display: none; }
  .search-results__actions { grid-column: 2; grid-row: 1 / span 2; justify-content: flex-end; width: auto; }
}
</style>
