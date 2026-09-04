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
.us-index-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  min-width: 0;
}

.us-index-strip__quote {
  display: grid;
  align-content: center;
  gap: var(--spacing-1);
  min-width: 0;
  padding: var(--spacing-3);
  border-left: 1px solid var(--border-subtle);
}

.us-index-strip__quote:first-child {
  border-left: 0;
}

.us-index-strip__name {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.us-index-strip__breadth {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, auto));
  align-content: center;
  gap: var(--spacing-6);
  padding: var(--spacing-3) var(--spacing-4);
  border-left: 1px solid var(--border-subtle);
}

.us-index-strip__breadth :deep(.metric-cell__value) {
  font-size: var(--font-size-2xl);
}

@media (max-width: 767px) {
  .us-index-strip {
    grid-template-columns: minmax(0, 1fr);
  }

  .us-index-strip__quote {
    border-left: 0;
    border-top: 1px solid var(--border-subtle);
  }

  .us-index-strip__quote:first-child {
    border-top: 0;
  }

  .us-index-strip__breadth {
    border-left: 0;
    border-top: 1px solid var(--border-subtle);
  }
}
</style>
