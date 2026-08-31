<template>
  <SectionPanel class="board-table" variant="flush">
    <template #header>
      <div class="board-table__header">
        <h3 class="board-table__title">{{ title }}</h3>
      </div>
    </template>

    <StatusState
      v-if="loading"
      state="loading"
      title="正在加载板块列表"
      description="行业与概念列表分开请求。"
      :min-height="260"
    />

    <StatusState
      v-else-if="error"
      state="error"
      title="板块列表加载失败"
      description="当前无法读取板块列表，可重新尝试。"
      :min-height="260"
      @retry="$emit('retry')"
    />

    <StatusState
      v-else-if="boards.length === 0"
      state="empty"
      title="暂无板块数据"
      description="当前筛选条件下没有可展示内容。"
      :min-height="260"
    />

    <div v-else class="board-table__rows">
      <div class="board-table__columns" aria-hidden="true">
        <span>板块</span>
        <span>成交额 / 换手 / 涨跌</span>
      </div>
      <button
        v-for="board in boards"
        :key="board.name"
        :class="['board-table__row', { 'is-selected': board.name === selectedName }]"
        type="button"
        @click="$emit('select', board)"
      >
        <div>
          <p class="board-table__name">{{ board.name }}</p>
          <p class="board-table__desc">
            领涨 {{ board.leading_stock || '--' }} · 上涨 {{ board.rise_count ?? '--' }} / 下跌 {{ board.fall_count ?? '--' }}
          </p>
        </div>

        <div class="board-table__metrics">
          <span class="board-table__metric">{{ formatYi(board.total_turnover) }}</span>
          <span class="board-table__metric">
            {{ board.turnover_rate == null ? '--' : formatPercent(board.turnover_rate, 2, false) }}
          </span>
          <PercentageDisplay :value="board.change_pct" size="sm" />
        </div>
      </button>
    </div>
  </SectionPanel>
</template>

<script setup>
import PercentageDisplay from '../base/PercentageDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import { formatPercent, formatYi } from '../../utils/format'

defineProps({
  title: {
    type: String,
    default: '板块列表',
  },
  boards: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Boolean,
    default: false,
  },
  selectedName: {
    type: String,
    default: '',
  },
})

defineEmits(['select', 'retry'])
</script>

<style scoped>
.board-table__header,
.board-table__row,
.board-table__metrics {
  display: flex;
  align-items: center;
}

.board-table__header,
.board-table__row {
  justify-content: space-between;
  gap: var(--spacing-4);
}

.board-table__desc {
  margin: 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.board-table__title,
.board-table__name {
  margin: 0;
  color: var(--text-primary);
}

.board-table__rows {
  display: grid;
}

.board-table__columns { display: flex; justify-content: space-between; gap: var(--spacing-3); min-height: var(--table-head-height); padding: 0 var(--spacing-3); color: var(--text-tertiary); font-size: var(--font-size-xs); line-height: var(--table-head-height); }

.board-table__row {
  min-height: var(--data-row-height);
  padding: 0 var(--spacing-3);
  border-bottom: 1px solid var(--border-subtle);
  background: transparent;
  border-left: 0;
  border-right: 0;
  border-top: 0;
  cursor: pointer;
  text-align: left;
}

.board-table__row:last-child {
  border-bottom: 0;
}

.board-table__row:hover { background: var(--state-hover); }
.board-table__row.is-selected { background: var(--state-selected); }

.board-table__metrics {
  gap: var(--spacing-3);
}

.board-table__metric {
  min-width: 80px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  text-align: right;
}

@media (max-width: 767px) {
  .board-table__columns { display: none; }

  .board-table__row {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--spacing-2);
    padding: var(--spacing-3);
  }

  .board-table__metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--spacing-2);
    width: 100%;
  }

  .board-table__metric {
    min-width: 0;
    overflow-wrap: anywhere;
    text-align: left;
  }
}
</style>
