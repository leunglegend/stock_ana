<template>
  <section class="watchlist-table">
    <el-table :data="rows" :row-key="(row) => row.code" v-loading="loading" table-layout="fixed">
      <el-table-column label="股票" min-width="190">
        <template #default="{ row }"><StockName :name="row.name" :code="row.code" /></template>
      </el-table-column>
      <el-table-column label="现价" width="98" align="right">
        <template #default="{ row }">
          <span v-if="row.quoteStatus === 'success'" class="watchlist-table__number">{{ formatPrice(row.price) }}</span>
          <span v-else class="watchlist-table__muted">{{ quoteStateLabel(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="涨跌" width="122" align="right">
        <template #default="{ row }">
          <span v-if="row.quoteStatus === 'success'" class="watchlist-table__number" :class="movementClass(row.changePct)">{{ formatPercent(row.changePct) }}</span>
          <span v-else class="watchlist-table__muted">--</span>
        </template>
      </el-table-column>
      <el-table-column label="成本收益" width="126" align="right">
        <template #default="{ row }">
          <span v-if="row.costReturn != null" class="watchlist-table__number" :class="movementClass(row.costReturn)">{{ formatPercent(row.costReturn * 100) }}</span>
          <span v-else class="watchlist-table__muted">--</span>
        </template>
      </el-table-column>
      <el-table-column label="信号" width="88" class-name="watchlist-table__desktop-detail" label-class-name="watchlist-table__desktop-detail">
        <template #default="{ row }"><TagBadge :type="signalType(row.code)" size="sm">{{ signalLabel(row.code) }}</TagBadge></template>
      </el-table-column>
      <el-table-column label="备注" min-width="150" class-name="watchlist-table__desktop-detail" label-class-name="watchlist-table__desktop-detail">
        <template #default="{ row }"><span class="watchlist-table__remark">{{ row.remark || '--' }}</span></template>
      </el-table-column>
      <el-table-column label="更新" width="106" align="right" class-name="watchlist-table__desktop-detail" label-class-name="watchlist-table__desktop-detail">
        <template #default="{ row }"><span class="watchlist-table__number watchlist-table__muted">{{ row.updatedAt ? formatFetchTime(row.updatedAt) : quoteStateLabel(row) }}</span></template>
      </el-table-column>
      <el-table-column label="更多" width="58" align="center" fixed="right">
        <template #default="{ row }">
          <el-dropdown trigger="click" @command="handleCommand($event, row)">
            <el-button text circle aria-label="更多操作"><el-icon><MoreFilled /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="open">查看详情</el-dropdown-item>
                <el-dropdown-item command="edit">编辑成本与备注</el-dropdown-item>
                <el-dropdown-item v-if="row.quoteStatus === 'error'" command="retry">重试行情</el-dropdown-item>
                <el-dropdown-item command="remove" divided>移除自选</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { MoreFilled } from '@element-plus/icons-vue'
import StockName from '@/components/base/StockName.vue'
import TagBadge from '@/components/base/TagBadge.vue'
import { formatFetchTime, formatPercent, formatPrice } from '@/utils/format'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  signals: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'edit', 'remove', 'retry'])
const signalMap = computed(() => new Map(props.signals.map((item) => [item.code, item])))

function quoteStateLabel(row) {
  return row.quoteStatus === 'loading' ? '加载中' : row.quoteStatus === 'error' ? '失败' : '--'
}

function movementClass(value) {
  if (value > 0) return 'is-up'
  if (value < 0) return 'is-down'
  return ''
}

function signalLabel(code) {
  const signal = signalMap.value.get(code)
  if (!signal) return '未扫描'
  if (signal.status === 'error') return '失败'
  return { strong: '偏强', neutral: '中性', attention: '关注' }[signal.analysis?.status] || '扫描中'
}

function signalType(code) {
  const signal = signalMap.value.get(code)
  if (signal?.status === 'error') return 'warning'
  return { strong: 'primary', neutral: 'default', attention: 'warning' }[signal?.analysis?.status] || 'info'
}

function handleCommand(command, row) {
  emit(command, command === 'retry' || command === 'open' ? row.code : row)
}
</script>

<style scoped>
.watchlist-table { min-width: 0; background: var(--surface-panel); }
.watchlist-table__number { font-family: var(--font-family-mono); font-variant-numeric: tabular-nums; }
.watchlist-table__remark, .watchlist-table__muted { color: var(--text-tertiary); }
.watchlist-table__remark { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.is-up { color: var(--text-positive); }
.is-down { color: var(--text-negative); }
:deep(.el-table .el-table__cell) { min-height: var(--data-row-height); height: var(--data-row-height); padding: 0; }
:deep(.el-table th.el-table__cell) { height: var(--table-head-height); padding: 0; }
@media (min-width: 768px) and (max-width: 1023px) {
  :deep(.watchlist-table__desktop-detail) { display: none; }
}
</style>
