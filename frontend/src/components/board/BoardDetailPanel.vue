<template>
  <component
    :is="detailContainer"
    v-bind="containerProps"
    class="board-detail"
    @close="$emit('close')"
  >
    <template v-if="mobile" #header>
      <div class="board-detail__header">
        <div>
          <h3 class="board-detail__title">{{ board?.name || '板块详情' }}</h3>
        </div>
        <PercentageDisplay :value="board?.change_pct" size="sm" />
      </div>
    </template>

    <template v-if="!mobile && !visible">
      <StatusState
        state="empty"
        title="选择一个板块查看成分股"
        description="从左侧列表选择行业或概念板块，详情将在此处展开。"
        :min-height="260"
      />
    </template>

    <template v-else>
      <div v-if="!mobile" class="board-detail__header">
        <div>
          <h3 class="board-detail__title">{{ board?.name || '板块详情' }}</h3>
        </div>
        <div class="board-detail__header-actions">
          <PercentageDisplay :value="board?.change_pct" size="sm" />
          <el-button circle text aria-label="关闭板块详情" @click="$emit('close')">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <div v-if="visible && board" class="board-detail__facts" aria-label="板块概览">
        <div class="board-detail__fact">
          <span class="board-detail__fact-label">总成交额</span>
          <strong>{{ formatYi(board.total_turnover) }}</strong>
        </div>
        <div class="board-detail__fact">
          <span class="board-detail__fact-label">换手率</span>
          <strong>{{ formatPercent(board.turnover_rate, 2, false) }}</strong>
        </div>
        <div class="board-detail__fact">
          <span class="board-detail__fact-label">上涨 / 下跌</span>
          <strong>{{ board.rise_count ?? '--' }} / {{ board.fall_count ?? '--' }}</strong>
        </div>
        <div class="board-detail__fact">
          <span class="board-detail__fact-label">覆盖个股</span>
          <strong>{{ board.stock_count ?? stocks.length ?? '--' }}</strong>
        </div>
        <div class="board-detail__fact">
          <span class="board-detail__fact-label">领涨</span>
          <strong>{{ board.leading_stock || '--' }}</strong>
        </div>
      </div>

      <div v-if="stocks.length > 0" class="board-detail__tools">
        <el-input
          v-model="stockKeyword"
          clearable
          aria-label="按成分股名称或代码筛选"
          placeholder="筛选名称或代码"
        />
        <el-select v-model="stockSortKey" class="board-detail__sort" aria-label="成分股排序方式">
          <el-option label="按涨跌幅" value="change_pct" />
          <el-option label="按价格" value="price" />
          <el-option label="按换手率" value="turnover_rate" />
        </el-select>
      </div>

      <StatusState
        v-if="loading"
        state="loading"
        title="正在加载成分股"
        description="只展示该板块接口返回的成分股字段。"
        :min-height="260"
      />

      <StatusState
        v-else-if="error"
        state="error"
        title="成分股加载失败"
        description="当前无法读取板块详情，可重新尝试。"
        :min-height="260"
        @retry="$emit('retry')"
      />

      <StatusState
        v-else-if="stocks.length === 0"
        state="empty"
        title="暂无成分股"
        description="接口当前没有返回该板块成分股。"
        :min-height="260"
      />

      <StatusState
        v-else-if="filteredStocks.length === 0"
        state="empty"
        title="未找到匹配的成分股"
        description="可调整名称、代码或排序条件后继续查看。"
        :min-height="260"
      />

      <div v-else class="board-detail__list">
        <button
          v-for="stock in paginatedStocks"
          :key="stock.code"
          class="board-detail__row"
          type="button"
          @click="$emit('open-stock', stock.code)"
        >
          <div>
            <p class="board-detail__name">{{ stock.name }}</p>
            <p class="board-detail__code">{{ stock.code }}</p>
          </div>

          <div class="board-detail__metrics">
            <span class="board-detail__metric">
              <span class="board-detail__metric-label">换手率</span>
              <span>{{ formatPercent(stock.turnover_rate, 2, false) }}</span>
            </span>
            <span class="board-detail__metric">
              <span class="board-detail__metric-label">PE</span>
              <span>{{ formatPeValue(stock.pe) }}</span>
            </span>
            <span class="board-detail__metric">
              <span class="board-detail__metric-label">市值</span>
              <span>{{ formatMv(stock.total_mv) }}</span>
            </span>
            <span class="board-detail__metric">
              <span class="board-detail__metric-label">价格/涨跌</span>
              <PriceDisplay
                :price="stock.price"
                :change="stock.change_amount"
                :change-percent="stock.change_pct"
                size="sm"
              />
            </span>
          </div>
        </button>
      </div>
      <footer v-if="filteredStocks.length > detailPageSize" class="board-detail__pagination">
        <span>共 {{ filteredStocks.length }} 只</span>
        <span v-if="mobile" class="board-detail__page-state">第 {{ detailPage }} / {{ detailPageCount }} 页</span>
        <el-pagination
          v-model:current-page="detailPage"
          :page-size="detailPageSize"
          :total="filteredStocks.length"
          :pager-count="mobile ? 3 : 5"
          background
          :layout="mobile ? 'prev, next' : 'prev, pager, next'"
          size="small"
        />
      </footer>
      <p v-else-if="filteredStocks.length" class="board-detail__total">共 {{ filteredStocks.length }} 只</p>
    </template>
  </component>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { ElDrawer } from 'element-plus'

import PercentageDisplay from '../base/PercentageDisplay.vue'
import PriceDisplay from '../base/PriceDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import { formatMv, formatPercent, formatYi, safeNumber } from '../../utils/format'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Boolean,
    default: false,
  },
  mobile: {
    type: Boolean,
    default: false,
  },
  board: {
    type: Object,
    default: null,
  },
  boardType: {
    type: String,
    default: 'industry',
  },
  stocks: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['close', 'retry', 'open-stock'])

const boardTypeLabel = computed(() => (props.boardType === 'concept' ? '概念板块' : '行业板块'))
const detailContainer = computed(() => (props.mobile ? ElDrawer : SectionPanel))
const detailPage = ref(1)
const detailPageSize = 10
const stockKeyword = ref('')
const stockSortKey = ref('change_pct')
const containerProps = computed(() => (
  props.mobile
    ? { modelValue: props.visible, direction: 'btt', size: '100%' }
    : { variant: 'flush' }
))
const paginatedStocks = computed(() => {
  const start = (detailPage.value - 1) * detailPageSize
  return sortedStocks.value.slice(start, start + detailPageSize)
})
const detailPageCount = computed(() => Math.ceil(filteredStocks.value.length / detailPageSize))

const filteredStocks = computed(() => {
  const keyword = stockKeyword.value.trim().toLowerCase()
  if (!keyword) return props.stocks
  return props.stocks.filter((stock) => (
    String(stock.name || '').toLowerCase().includes(keyword)
    || String(stock.code || '').toLowerCase().includes(keyword)
  ))
})

const sortedStocks = computed(() => [...filteredStocks.value].sort((left, right) => (
  stockSortValue(right) - stockSortValue(left)
)))

watch([stockKeyword, stockSortKey, () => props.stocks, () => props.board?.name, () => props.boardType, () => props.visible], () => {
  detailPage.value = 1
})

function formatPeValue(value) {
  const num = safeNumber(value)
  return num == null ? '--' : num.toFixed(2)
}

function stockSortValue(stock) {
  const value = safeNumber(stock[stockSortKey.value])
  return value == null ? Number.NEGATIVE_INFINITY : value
}
</script>

<style scoped>
.board-detail__header, .board-detail__header-actions, .board-detail__row, .board-detail__metrics { display: flex; align-items: center; }
.board-detail__header, .board-detail__row { justify-content: space-between; gap: var(--spacing-4); }
.board-detail__header-actions { gap: var(--spacing-2); }
.board-detail:not(.el-drawer) :deep(.section-panel__header) { display: none; }
.board-detail:not(.el-drawer) :deep(.section-panel__body) { padding: 0; }
.board-detail:not(.el-drawer) .board-detail__header { padding: var(--spacing-3) var(--spacing-4); border-bottom: 1px solid var(--border-subtle); }
.board-detail:not(.el-drawer) :deep(.status-state) { padding-inline: var(--spacing-4); }
.board-detail__facts { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0; border-bottom: 1px solid var(--border-subtle); }
.board-detail__fact { display: grid; align-content: center; gap: var(--spacing-1); min-width: 0; min-height: 56px; padding: var(--spacing-2) var(--spacing-3); border-right: 1px solid var(--border-subtle); }
.board-detail__fact:last-child { border-right: 0; }
.board-detail__fact-label { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.board-detail__fact strong { overflow-wrap: anywhere; color: var(--text-primary); font-size: var(--font-size-sm); font-variant-numeric: tabular-nums; line-height: 1.25; }
.board-detail__tools { display: flex; align-items: center; gap: var(--spacing-2); padding: var(--spacing-3) var(--spacing-4); border-bottom: 1px solid var(--border-subtle); }
.board-detail__tools :deep(.el-input) { flex: 1; min-width: 0; }
.board-detail__sort { width: 156px; }
.board-detail__code { margin: 0; color: var(--text-tertiary); font-size: var(--font-size-sm); }
.board-detail__title, .board-detail__name { margin: 0; color: var(--text-primary); }
.board-detail__list { display: grid; padding: 0 var(--spacing-4); }
.board-detail__pagination, .board-detail__total { display: flex; align-items: center; justify-content: flex-end; gap: var(--spacing-3); margin: 0; padding: var(--spacing-3) var(--spacing-4); border-top: 1px solid var(--border-subtle); color: var(--text-tertiary); font-size: var(--font-size-sm); }
.board-detail__page-state { font-size: var(--font-size-xs); }
.board-detail__row { min-height: 56px; padding: 0; border: 0; border-bottom: 1px solid var(--border-subtle); background: transparent; cursor: pointer; text-align: left; }
.board-detail__metrics { display: grid; grid-template-columns: repeat(4, minmax(0, auto)); gap: var(--spacing-3); min-width: 0; color: var(--text-secondary); font-size: var(--font-size-sm); }
.board-detail__metric { display: grid; gap: var(--spacing-1); min-width: 0; white-space: nowrap; }
.board-detail__metric-label { color: var(--text-tertiary); font-size: var(--font-size-xs); }

@media (max-width: 767px) {
  .board-detail__facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .board-detail__fact { min-height: 52px; border-bottom: 1px solid var(--border-subtle); }
  .board-detail__fact:nth-child(2n) { border-right: 0; }
  .board-detail__fact:last-child { grid-column: span 2; border-bottom: 0; }
  .board-detail__tools { flex-wrap: wrap; }
  .board-detail__tools :deep(.el-input__wrapper), .board-detail__tools :deep(.el-select__wrapper) { min-height: 44px; touch-action: manipulation; }
  .board-detail__sort { flex: 1 1 140px; }
  .board-detail__row { display: grid; grid-template-columns: 1fr; padding: var(--spacing-4) 0; }
  .board-detail__metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--spacing-2) var(--spacing-3); }
  .board-detail__metric :deep(.price-display) { display: grid; align-items: start; gap: var(--spacing-1); }
  .board-detail__pagination { justify-content: space-between; }
}
</style>
