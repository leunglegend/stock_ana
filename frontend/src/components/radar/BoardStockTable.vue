<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="board-stock-table__header">
        <div>
          <span class="board-stock-table__context-label">{{ board?.name || '当前板块' }}</span>
          <h3 class="board-stock-table__title">候选股票</h3>
        </div>
        <div class="board-stock-table__meta">
          <span>{{ resolvedTotal }} 只</span>
          <span v-if="refreshing" class="board-stock-table__meta-status">更新中</span>
        </div>
      </div>
    </template>

    <StatusState
      v-if="!board && !loading"
      state="empty"
      title="选择板块后查看成分股"
      description="从左侧榜单选择行业或概念板块，这里会展示对应股票。"
      :min-height="320"
    />

    <StatusState
      v-else-if="loading && !hasStocks"
      state="loading"
      title="正在加载成分股"
      description="只请求当前选中板块，不会扫描全部板块。"
      :min-height="320"
    />

    <StatusState
      v-else-if="error && !hasStocks"
      state="error"
      title="成分股加载失败"
      description="当前无法读取这个板块的股票列表，可单独重试。"
      :min-height="320"
      @retry="$emit('retry')"
    />

    <StatusState
      v-else-if="!hasStocks"
      state="empty"
      title="暂无成分股数据"
      description="接口当前没有返回这个板块的成分股。"
      :min-height="320"
    />

    <div v-else class="board-stock-table__body">
      <div
        v-if="refreshing || error"
        class="board-stock-table__notice"
        :class="{ 'is-error': !!error }"
        role="status"
        aria-live="polite"
      >
        <span>{{ noticeLabel }}</span>
        <el-button v-if="error" link type="primary" @click="$emit('retry')">重试当前板块</el-button>
      </div>

      <div v-if="!mobile" class="board-stock-table__desktop">
        <el-table :data="currentRows" :row-key="(row) => row.code" table-layout="auto">
          <el-table-column label="股票" min-width="180">
            <template #default="{ row }">
              <StockName :name="row.name" :code="row.code" />
            </template>
          </el-table-column>

          <el-table-column label="最新价" width="100" align="right">
            <template #default="{ row }">
              <span class="board-stock-table__mono">{{ priceLabel(row.price) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="涨跌幅" width="100" align="right">
            <template #default="{ row }">
              <PercentageDisplay :value="row.change_pct" size="sm" />
            </template>
          </el-table-column>

          <el-table-column label="换手率" width="100" align="right">
            <template #default="{ row }">
              <span class="board-stock-table__mono">{{ turnoverRateLabel(row.turnover_rate) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="信号" width="84" align="center">
            <template #default="{ row }">
              <span class="board-stock-table__signal">{{ signalLabel(row.change_pct) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" min-width="180" fixed="right">
            <template #default="{ row }">
              <div class="board-stock-table__actions">
                <el-button
                  link
                  type="primary"
                  :aria-label="`查看${row.name}详情`"
                  @click="$emit('open-stock', row.code)"
                >
                  <el-icon><ArrowRight /></el-icon>
                  查看详情
                </el-button>
                <el-button
                  link
                  type="primary"
                  :loading="addingCode === row.code"
                  :disabled="Boolean(addingCode) && addingCode !== row.code"
                  :aria-label="`加入自选：${row.name}`"
                  @click="$emit('add-watchlist', row)"
                >
                  <el-icon><Plus /></el-icon>
                  加入自选
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else class="board-stock-table__mobile" role="list" aria-label="板块成分股移动列表">
        <article
          v-for="row in currentRows"
          :key="row.code"
          class="board-stock-table__mobile-row"
          role="listitem"
        >
          <button
            type="button"
            class="board-stock-table__mobile-identity"
            :aria-label="`查看${row.name}详情`"
            @click="$emit('open-stock', row.code)"
          >
            <StockName :name="row.name" :code="row.code" />
          </button>
          <div class="board-stock-table__mobile-quote" aria-label="最新价与涨跌幅">
            <span class="board-stock-table__mono">{{ priceLabel(row.price) }}</span>
            <PercentageDisplay :value="row.change_pct" size="sm" />
          </div>
          <span class="board-stock-table__signal" aria-label="信号">{{ signalLabel(row.change_pct) }}</span>
          <el-button link type="primary" :loading="addingCode === row.code" :disabled="Boolean(addingCode) && addingCode !== row.code" :aria-label="`加入自选：${row.name}`" @click="$emit('add-watchlist', row)">加入</el-button>
        </article>
      </div>
    </div>

    <template v-if="hasStocks" #footer>
      <div class="board-stock-table__footer">
        <span>共 {{ resolvedTotal }} 只</span>
        <span v-if="compact" class="board-stock-table__page-state">第 {{ page }} / {{ pageCount }} 页</span>
        <el-pagination
          v-if="resolvedTotal > pageSize"
          :current-page="page"
          :page-size="pageSize"
          :total="resolvedTotal"
          :pager-count="5"
          background
          :layout="compact ? 'prev, next' : 'prev, pager, next'"
          small
          @update:current-page="$emit('page-change', $event)"
        />
      </div>
    </template>
  </SectionPanel>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowRight, Plus } from '@element-plus/icons-vue'

import PercentageDisplay from '@/components/base/PercentageDisplay.vue'
import SectionPanel from '@/components/base/SectionPanel.vue'
import StatusState from '@/components/base/StatusState.vue'
import StockName from '@/components/base/StockName.vue'
import { formatPercent, formatPrice, safeNumber } from '@/utils/format'
import { getStockSignal, paginateRows } from '@/utils/opportunityRadar'

const props = defineProps({
  board: { type: Object, default: null },
  rows: { type: Array, default: () => [] },
  stocks: { type: Array, default: () => [] },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  mobile: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  error: { type: [Boolean, String], default: false },
  refreshing: { type: Boolean, default: false },
  addingCode: { type: String, default: '' },
})

defineEmits(['open-stock', 'add-watchlist', 'retry', 'page-change'])

const resolvedTotal = computed(() => {
  const total = safeNumber(props.total)
  if (total != null && total > 0) return total
  return props.stocks.length || props.rows.length
})
const currentRows = computed(() => props.rows.length ? props.rows : paginateRows(props.stocks, props.page, props.pageSize))
const hasStocks = computed(() => currentRows.value.length > 0)
const pageCount = computed(() => Math.max(1, Math.ceil(resolvedTotal.value / props.pageSize)))
const noticeLabel = computed(() => (
  props.error
    ? '成分股更新失败，当前保留上次成功的数据。'
    : '成分股正在刷新，表格保留上次成功的数据。'
))

function priceLabel(value) {
  const number = safeNumber(value)
  return number == null ? '--' : formatPrice(number)
}

function turnoverRateLabel(value) {
  const number = safeNumber(value)
  return number == null ? '--' : formatPercent(number, 2, false)
}

function signalLabel(value) {
  return getStockSignal(value)
}
</script>

<style scoped>
.board-stock-table__header,.board-stock-table__footer{display:flex;align-items:center;justify-content:space-between;gap:var(--spacing-3)}
.board-stock-table__meta,.board-stock-table__meta-status,.board-stock-table__notice,.board-stock-table__footer,.board-stock-table__context-label{color:var(--text-tertiary);font-size:var(--font-size-sm);line-height:var(--line-height-normal)}
.board-stock-table__title{margin:0;color:var(--text-primary)}
.board-stock-table__meta{display:flex;align-items:center;gap:var(--spacing-2)}
.board-stock-table__body,.board-stock-table__mobile{display:grid;gap:var(--spacing-2)}
.board-stock-table__notice{display:flex;align-items:center;justify-content:space-between;gap:var(--spacing-3);padding:var(--spacing-2) var(--spacing-3);border-bottom:1px solid var(--border-subtle);background:var(--surface-info)}
.board-stock-table__notice.is-error{background:var(--surface-warning)}
.board-stock-table__actions{display:flex;align-items:center;gap:var(--spacing-1);flex-wrap:wrap}
.board-stock-table__footer{width:100%}
.board-stock-table__mono{font-family:var(--font-family-mono);font-variant-numeric:tabular-nums;color:var(--text-secondary)}
.board-stock-table__signal{display:inline-flex;align-items:center;justify-content:center;min-width:40px;padding:2px var(--spacing-1);border:1px solid var(--border-subtle);color:var(--text-secondary);font-size:var(--font-size-xs);font-weight:600;line-height:var(--line-height-normal);white-space:nowrap}
.board-stock-table__mobile-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto auto;align-items:center;gap:var(--spacing-2);min-height:72px;padding:0 var(--spacing-3);border-bottom:1px solid var(--border-subtle)}
.board-stock-table__mobile-identity{min-width:0;min-height:44px;padding:0;border:0;background:transparent;color:inherit;text-align:left;cursor:pointer}.board-stock-table__mobile-identity :deep(.stock-name){align-items:flex-start}.board-stock-table__mobile-quote{display:grid;justify-items:end;gap:2px;white-space:nowrap}
@media (max-width:767px){.board-stock-table__header,.board-stock-table__footer,.board-stock-table__notice{display:grid;grid-template-columns:minmax(0,1fr)}.board-stock-table__meta{justify-content:space-between}.board-stock-table__mobile-row{gap:var(--spacing-1);padding:0 var(--spacing-2)}}
</style>
