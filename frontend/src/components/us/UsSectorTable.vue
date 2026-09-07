<template>
  <BoardTable
    title="GICS 行业板块"
    loading-description="正在读取美股行业板块。"
    :boards="boards"
    :loading="loading"
    :error="error"
    :selected-name="selectedName"
    @select="$emit('select', $event)"
    @retry="$emit('retry')"
  >
    <template #note>
      <span class="us-sector-table__note">标普500成分等权聚合 · 非官方板块指数</span>
    </template>
    <template #columns>成分股 / 领涨幅 / 涨跌</template>
    <template #name="{ board }">
      {{ board.name }} <span class="us-sector-table__en">{{ board.name_en }}</span>
    </template>
    <template #metrics="{ board }">
      <span class="us-sector-table__metric">{{ board.stock_count ?? '--' }} 只</span>
      <span class="us-sector-table__metric">{{ formatChangePct(board.leading_change_pct) }}</span>
    </template>
  </BoardTable>
</template>

<script setup>
import { computed } from 'vue'
import BoardTable from '../board/BoardTable.vue'
import { formatChangePct } from '../../utils/format'
import { toUsBoard } from '../../utils/usBoardPresentation'

const props = defineProps({
  sectors: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  selectedName: { type: String, default: '' },
})
defineEmits(['select', 'retry'])
const boards = computed(() => props.sectors.map(toUsBoard))
</script>

<style scoped>
.us-sector-table__note, .us-sector-table__en { color: var(--text-tertiary); font-size: var(--font-size-xs); font-weight: 400; }
.us-sector-table__note { text-align: right; }
.us-sector-table__en { margin-left: var(--spacing-2); }
.us-sector-table__metric { min-width: 80px; color: var(--text-secondary); font-size: var(--font-size-sm); text-align: right; }
@media (max-width: 767px) {
  .us-sector-table__metric { min-width: 0; text-align: left; }
}
</style>
