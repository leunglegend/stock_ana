<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="us-sector-table__head">
        <span class="us-sector-table__title">GICS 行业板块</span>
        <span class="us-sector-table__note">标普500成分等权聚合 · 非官方板块指数</span>
      </div>
    </template>

    <StatusState v-if="error" state="error" title="板块加载失败" :min-height="220" @retry="$emit('retry')" />
    <StatusState v-else-if="loading" state="loading" title="正在加载板块列表" :min-height="220" />
    <template v-else-if="sectors.length">
      <div class="us-sector-list" role="list">
        <button
          v-for="s in sectors"
          :key="s.name"
          type="button"
          class="us-sector-row"
          :class="{ 'us-sector-row--active': s.name === selectedName }"
          role="listitem"
          @click="$emit('select', s)"
        >
          <span class="us-sector-row__main">
            <span class="us-sector-row__name">
              {{ s.name }}
              <i class="us-sector-row__en">{{ s.name_en }}</i>
            </span>
            <span class="us-sector-row__meta">
              领涨 {{ s.leading_symbol }} {{ formatChangePct(s.leading_change_pct) }}
              · 涨 {{ s.advancers }} / 跌 {{ s.decliners }}
            </span>
          </span>
          <PercentageDisplay :value="s.change_pct" size="md" />
        </button>
      </div>
    </template>
    <StatusState v-else state="empty" title="暂无板块数据" :min-height="220" />
  </SectionPanel>
</template>

<script setup>
import PercentageDisplay from '../base/PercentageDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import { formatChangePct } from '../../utils/format'

defineProps({
  sectors: {
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
.us-sector-table__head {
  display: grid;
  gap: var(--spacing-1);
  min-width: 0;
}

.us-sector-table__title {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-base);
  font-weight: 600;
}

.us-sector-table__note {
  margin: 0;
  overflow: hidden;
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.us-sector-list {
  display: grid;
}

.us-sector-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-4);
  width: 100%;
  min-height: var(--data-row-height);
  padding: var(--spacing-2) var(--spacing-3);
  border: 0;
  border-bottom: 1px solid var(--border-subtle);
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.us-sector-row:last-child {
  border-bottom: 0;
}

.us-sector-row:hover {
  background: var(--state-hover);
}

.us-sector-row--active {
  background: var(--state-selected);
}

.us-sector-row__main {
  display: grid;
  gap: var(--spacing-1);
  min-width: 0;
}

.us-sector-row__name {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 var(--spacing-2);
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-base);
  font-weight: 600;
}

.us-sector-row__en {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  font-style: normal;
  font-weight: 400;
}

.us-sector-row__meta {
  margin: 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

@media (max-width: 767px) {
  .us-sector-row {
    min-height: 56px;
    padding: var(--spacing-2) var(--spacing-3);
  }
}
</style>
