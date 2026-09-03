<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="us-snapshot__header">
        <div class="us-snapshot__heading">
          <h3 class="us-snapshot__title">美股收盘</h3>
          <span v-if="summary?.as_of" class="us-snapshot__scope">
            按标普500成分统计 · 美东 {{ summary.as_of }} 收盘
          </span>
        </div>
        <el-button link type="primary" class="us-snapshot__link" @click="$emit('open')">
          进入美股复盘 →
        </el-button>
      </div>
    </template>

    <StatusState
      v-if="error"
      state="error"
      title="美股收盘数据不可用"
      description="当前无法读取美股收盘概览，可重新尝试。"
      :min-height="180"
      @retry="$emit('retry')"
    />

    <StatusState v-else-if="loading && !summary" state="loading" :min-height="180" />

    <template v-else-if="summary && summary.indices && summary.indices.length">
      <div class="us-snapshot__quotes">
        <div v-for="idx in summary.indices" :key="idx.symbol" class="us-snapshot__quote">
          <span class="us-snapshot__quote-name">{{ idx.name }}</span>
          <PriceDisplay
            :price="safeNumber(idx.value)"
            :change="safeNumber(idx.change_amount)"
            :change-percent="safeNumber(idx.change_pct)"
            size="md"
          />
        </div>
      </div>

      <div v-if="gainers.length || losers.length" class="us-snapshot__groups">
        <div v-if="gainers.length" class="us-snapshot__group">
          <span class="us-snapshot__group-label">领涨板块</span>
          <div class="us-snapshot__group-chips">
            <button
              v-for="s in gainers"
              :key="s.name"
              type="button"
              class="us-snapshot__chip"
              :aria-label="`查看${s.name}板块`"
              @click="$emit('sector', s.name)"
            >
              <span class="us-snapshot__chip-name">{{ s.name }}</span>
              <PercentageDisplay :value="s.change_pct" size="sm" />
            </button>
          </div>
        </div>
        <div v-if="losers.length" class="us-snapshot__group">
          <span class="us-snapshot__group-label">领跌板块</span>
          <div class="us-snapshot__group-chips">
            <button
              v-for="s in losers"
              :key="s.name"
              type="button"
              class="us-snapshot__chip"
              :aria-label="`查看${s.name}板块`"
              @click="$emit('sector', s.name)"
            >
              <span class="us-snapshot__chip-name">{{ s.name }}</span>
              <PercentageDisplay :value="s.change_pct" size="sm" />
            </button>
          </div>
        </div>
      </div>
    </template>

    <StatusState v-else state="empty" title="暂无美股数据" :min-height="180" />
  </SectionPanel>
</template>

<script setup>
import { computed } from 'vue'

import PercentageDisplay from '../base/PercentageDisplay.vue'
import PriceDisplay from '../base/PriceDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import { safeNumber } from '../../utils/format'

const props = defineProps({
  summary: {
    type: Object,
    default: null,
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

defineEmits(['retry', 'open', 'sector'])

const gainers = computed(() => (props.summary?.top_gainers || []).slice(0, 3))
const losers = computed(() => (props.summary?.top_losers || []).slice(0, 3))
</script>

<style scoped>
.us-snapshot__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
}

.us-snapshot__heading {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.us-snapshot__title {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-base);
  font-weight: 600;
}

.us-snapshot__scope {
  overflow: hidden;
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.us-snapshot__link {
  flex-shrink: 0;
}

.us-snapshot__quotes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.us-snapshot__quote {
  display: grid;
  align-content: center;
  gap: var(--spacing-1);
  min-width: 0;
  min-height: 76px;
  padding: var(--spacing-3);
  border-left: 1px solid var(--border-subtle);
}

.us-snapshot__quote:first-child {
  border-left: 0;
}

.us-snapshot__quote-name {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.us-snapshot__groups {
  display: grid;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  border-top: 1px solid var(--border-subtle);
}

.us-snapshot__group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  min-width: 0;
}

.us-snapshot__group-label {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.us-snapshot__group-chips {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  min-width: 0;
}

.us-snapshot__chip {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  min-height: 28px;
  padding: var(--spacing-1) var(--spacing-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-pill);
  background: var(--surface-panel-muted);
  color: var(--text-secondary);
  cursor: pointer;
}

.us-snapshot__chip:hover {
  background: var(--state-hover);
  border-color: var(--border-default);
}

.us-snapshot__chip-name {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

@media (max-width: 767px) {
  .us-snapshot__quotes {
    grid-template-columns: minmax(0, 1fr);
  }

  .us-snapshot__quote {
    border-left: 0;
    border-top: 1px solid var(--border-subtle);
    min-height: 64px;
  }

  .us-snapshot__quote:first-child {
    border-top: 0;
  }

  .us-snapshot__chip ~ .us-snapshot__chip {
    display: none;
  }
}
</style>
