<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="top-boards__header">
        <div>
          <h3 class="top-boards__title">板块强弱</h3>
        </div>
        <el-button link type="primary" @click="$emit('view-all')">查看全部</el-button>
      </div>
    </template>

    <StatusState
      v-if="loading"
      state="loading"
      title="正在拉取板块数据"
      description="只展示现有行业接口返回的数据。"
      :min-height="220"
    />

    <StatusState
      v-else-if="error"
      state="error"
      title="板块数据不可用"
      description="当前无法读取行业板块列表，可稍后重试。"
      :min-height="220"
      @retry="$emit('retry')"
    />

    <table v-else-if="boards.length > 0" class="top-boards__table">
      <thead>
        <tr>
          <th>板块</th>
          <th>领涨股</th>
          <th class="top-boards__number">涨跌幅</th>
          <th class="top-boards__number top-boards__wide">上涨 / 下跌</th>
          <th class="top-boards__number top-boards__wide">成交额</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="board in boards"
          :key="board.name"
          tabindex="0"
          @click="$emit('select', board)"
          @keydown.enter="$emit('select', board)"
        >
          <td class="top-boards__name">{{ board.name }}</td>
          <td>{{ board.leading_stock || '--' }}</td>
          <td class="top-boards__number"><PercentageDisplay :value="board.change_pct" size="sm" /></td>
          <td class="top-boards__number top-boards__wide">{{ board.rise_count ?? '--' }} / {{ board.fall_count ?? '--' }}</td>
          <td class="top-boards__number top-boards__wide">{{ formatYi(board.total_turnover) }}</td>
        </tr>
      </tbody>
    </table>

    <StatusState
      v-else
      state="empty"
      title="暂无行业数据"
      description="接口当前没有返回可展示的板块。"
      :min-height="220"
    />
  </SectionPanel>
</template>

<script setup>
import PercentageDisplay from '../base/PercentageDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import { formatYi } from '../../utils/format'

defineProps({
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
})

defineEmits(['retry', 'select', 'view-all'])
</script>

<style scoped>
.top-boards__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
}

.top-boards__title { margin: 0; color: var(--text-primary); font-size: var(--font-size-base); }

.top-boards__table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.top-boards__table th {
  height: 32px;
  padding: 0 var(--spacing-3);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-panel-muted);
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-align: left;
}

.top-boards__table td {
  height: 40px;
  padding: 0 var(--spacing-3);
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-boards__table tbody tr { cursor: pointer; }
.top-boards__table tbody tr:hover td,
.top-boards__table tbody tr:focus-visible td { background: var(--state-hover); }
.top-boards__name {
  color: var(--text-primary) !important;
  font-size: var(--font-size-base);
  font-weight: 600;
}
.top-boards__number { text-align: right !important; font-family: var(--font-family-mono); }
.top-boards__number :deep(.price-display) { justify-content: flex-end; }

@media (max-width: 767px) {
  .top-boards__wide { display: none; }
}
</style>
