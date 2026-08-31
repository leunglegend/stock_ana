<template>
  <section class="board-snapshot board-snapshot--context" aria-label="当前板块上下文">
    <template v-if="board">
      <div class="board-snapshot__identity">
        <div>
          <span class="board-snapshot__context-label">{{ boardTypeLabel }}</span>
          <h2 class="board-snapshot__title">{{ board.name }}</h2>
        </div>
        <div class="board-snapshot__move">
          <PercentageDisplay :value="board.change_pct" size="lg" />
          <span v-if="refreshing" class="board-snapshot__status">更新中</span>
        </div>
      </div>

      <dl class="board-snapshot__facts">
        <div class="board-snapshot__fact">
          <dt>领涨股</dt>
          <dd>{{ board.leading_stock || '--' }} {{ leadingChangeLabel }}</dd>
        </div>
        <div class="board-snapshot__fact">
          <dt>总成交额</dt>
          <dd>{{ turnoverLabel }}</dd>
        </div>
        <div class="board-snapshot__fact">
          <dt>换手率</dt>
          <dd>{{ turnoverRateLabel }}</dd>
        </div>
        <div class="board-snapshot__fact">
          <dt>上涨 / 下跌</dt>
          <dd>{{ countLabel(board.rise_count) }} / {{ countLabel(board.fall_count) }}</dd>
        </div>
        <div class="board-snapshot__fact">
          <dt>覆盖个股</dt>
          <dd>{{ countLabel(board.stock_count) }}</dd>
        </div>
        <div class="board-snapshot__fact">
          <dt>最近同步</dt>
          <dd>{{ updatedLabel }}</dd>
        </div>
      </dl>
    </template>
    <p v-else class="board-snapshot__empty">选择左侧板块后查看候选股票。</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import PercentageDisplay from '@/components/base/PercentageDisplay.vue'
import { formatFetchTime, formatPercent, formatYi, safeNumber } from '@/utils/format'

const props = defineProps({
  board: {
    type: Object,
    default: null,
  },
  type: {
    type: String,
    default: '',
  },
  boardType: {
    type: String,
    default: 'industry',
  },
  refreshing: {
    type: Boolean,
    default: false,
  },
  updatedAt: {
    type: [Number, String, Date],
    default: null,
  },
})

const boardTypeLabel = computed(() => (
  (props.type || props.boardType) === 'concept' ? '概念板块' : '行业板块'
))
const updatedLabel = computed(() => (
  props.updatedAt == null ? '--' : formatFetchTime(props.updatedAt)
))
const turnoverLabel = computed(() => {
  const number = safeNumber(props.board?.total_turnover)
  return number == null ? '--' : formatYi(number)
})
const turnoverRateLabel = computed(() => {
  const number = safeNumber(props.board?.turnover_rate)
  return number == null ? '--' : formatPercent(number, 2, false)
})
const leadingChangeLabel = computed(() => {
  const number = safeNumber(props.board?.leading_change)
  return number == null ? '--' : formatPercent(number, 2, true)
})

function countLabel(value) {
  const number = safeNumber(value)
  return number == null ? '--' : `${number}`
}
</script>

<style scoped>
.board-snapshot--context {
  display: grid;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-panel-muted);
}

.board-snapshot__identity,
.board-snapshot__move {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
}

.board-snapshot__move { justify-content: flex-end; }

.board-snapshot__context-label,
.board-snapshot__status,
.board-snapshot__empty,
.board-snapshot__fact dt {
  margin: 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
}

.board-snapshot__title {
  margin: 2px 0 0;
  color: var(--text-primary);
  font-size: var(--font-size-lg);
  line-height: var(--line-height-tight);
}

.board-snapshot__facts {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--spacing-2);
  margin: 0;
}

.board-snapshot__fact { min-width: 0; }
.board-snapshot__fact dd {
  margin: 4px 0 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  line-height: var(--line-height-normal);
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .board-snapshot--context { padding: var(--spacing-3); }
  .board-snapshot__identity {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }
  .board-snapshot__move { justify-content: space-between; }
  .board-snapshot__facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
