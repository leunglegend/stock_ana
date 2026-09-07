<template>
  <div class="us-index-strip" data-testid="us-index-strip">
    <template v-if="summary && summary.indices && summary.indices.length">
      <div v-for="idx in summary.indices" :key="idx.symbol" class="us-index-strip__quote">
        <span class="us-index-strip__name">{{ idx.name }}</span>
        <PriceDisplay
          :price="safeNumber(idx.value)"
          :change="safeNumber(idx.change_amount)"
          :change-percent="safeNumber(idx.change_pct)"
          size="md"
        />
      </div>
      <div class="us-index-strip__breadth">
        <MetricCell label="成分上涨" :value="formatThousands(summary.advancers)" tone="positive" />
        <MetricCell label="成分下跌" :value="formatThousands(summary.decliners)" tone="negative" />
      </div>
    </template>
    <StatusState v-else-if="loading" state="loading" :min-height="72" />
    <StatusState v-else state="empty" title="暂无美股数据" :min-height="72" />
  </div>
</template>

<script setup>
import MetricCell from '../base/MetricCell.vue'
import PriceDisplay from '../base/PriceDisplay.vue'
import StatusState from '../base/StatusState.vue'
import { formatThousands, safeNumber } from '../../utils/format'

defineProps({
  summary: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
/* 摘要条与板块行 toolbar 等高：指数名、点位、涨跌同一条基线上横排，
   涨跌计数也压成横向「上涨/下跌」小值，避免顶部形成竖排大数字的高垛。 */
.us-index-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  column-gap: var(--spacing-5);
  row-gap: var(--spacing-1);
  min-width: 0;
  padding: var(--spacing-2) var(--spacing-4);
}

.us-index-strip__quote {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-2);
  min-width: 0;
}

.us-index-strip__name {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

.us-index-strip__breadth {
  display: flex;
  align-items: baseline;
  margin-left: auto;
}

.us-index-strip__breadth :deep(.metric-cell) {
  display: grid;
  grid-template-columns: auto auto;
  column-gap: var(--spacing-1);
  align-items: baseline;
  gap: 0;
}

.us-index-strip__breadth :deep(.metric-cell + .metric-cell) {
  margin-left: var(--spacing-5);
  padding-left: var(--spacing-5);
  border-left: 1px solid var(--border-subtle);
}

.us-index-strip__breadth :deep(.metric-cell__label) {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.us-index-strip__breadth :deep(.metric-cell__value) {
  font-size: var(--font-size-xl);
  font-weight: 600;
  line-height: var(--line-height-normal);
}

@media (max-width: 767px) {
  .us-index-strip {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--spacing-2);
    padding-block: var(--spacing-3);
  }

  .us-index-strip__quote {
    flex-wrap: wrap;
  }

  .us-index-strip__breadth {
    margin-left: 0;
    padding-top: var(--spacing-1);
    border-top: 1px solid var(--border-subtle);
  }

  .us-index-strip__breadth :deep(.metric-cell + .metric-cell) {
    margin-left: var(--spacing-4);
    padding-left: var(--spacing-4);
  }
}
</style>
