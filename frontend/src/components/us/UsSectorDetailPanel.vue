<template>
  <component
    :is="detailContainer"
    v-bind="containerProps"
    class="us-sector-detail"
    @close="$emit('close')"
  >
    <template v-if="mobile" #header>
      <div class="us-sector-detail__head">
        <h3 class="us-sector-detail__title">{{ board?.name || '板块详情' }}</h3>
        <PercentageDisplay :value="board?.change_pct" size="sm" />
      </div>
    </template>

    <template v-if="!mobile && !visible">
      <StatusState
        state="empty"
        title="选择一个板块查看成分股"
        description="从左侧全量板块榜选择行业板块，成分股将在此处展开。"
        :min-height="260"
      />
    </template>

    <template v-else>
      <div v-if="!mobile" class="us-sector-detail__head us-sector-detail__head--inner">
        <h3 class="us-sector-detail__title">{{ board?.name || '板块详情' }}</h3>
        <div class="us-sector-detail__head-actions">
          <PercentageDisplay :value="board?.change_pct" size="sm" />
          <el-button circle text aria-label="关闭板块详情" @click="$emit('close')">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <div v-if="visible && board" class="us-sector-detail__facts" aria-label="板块概览">
        <div class="us-sector-detail__fact">
          <span class="us-sector-detail__fact-label">领涨</span>
          <strong>{{ board.leading_symbol || '--' }}</strong>
        </div>
        <div class="us-sector-detail__fact">
          <span class="us-sector-detail__fact-label">上涨 / 下跌</span>
          <strong>{{ board.advancers ?? '--' }} / {{ board.decliners ?? '--' }}</strong>
        </div>
        <div class="us-sector-detail__fact">
          <span class="us-sector-detail__fact-label">成分股</span>
          <strong>{{ board.constituent_count ?? '--' }}</strong>
        </div>
      </div>

      <StatusState
        v-if="loading"
        state="loading"
        title="正在加载成分股"
        description="板块成分按涨跌幅降序返回。"
        :min-height="220"
      />

      <StatusState
        v-else-if="error"
        state="error"
        title="成分股加载失败"
        description="当前无法读取板块成分，可重新尝试。"
        :min-height="220"
        @retry="$emit('retry')"
      />

      <StatusState
        v-else-if="stocks.length === 0"
        state="empty"
        title="暂无成分股"
        description="该板块接口当前没有返回成分。"
        :min-height="220"
      />

      <div v-else class="us-sector-detail__list">
        <button
          v-for="s in stocks"
          :key="s.symbol"
          type="button"
          class="us-sector-detail__row"
          @click="$emit('open-symbol', s.symbol)"
        >
          <StockName :name="s.name" :code="s.symbol" />
          <PercentageDisplay :value="s.change_pct" size="sm" />
        </button>
        <p class="us-sector-detail__total">共 {{ stocks.length }} 只</p>
      </div>
    </template>
  </component>
</template>

<script setup>
import { computed } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { ElDrawer } from 'element-plus'

import PercentageDisplay from '../base/PercentageDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import StockName from '../base/StockName.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Boolean,
    default: false,
  },
  mobile: {
    type: Boolean,
    default: false,
  },
  board: {
    type: Object,
    default: null,
  },
  stocks: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['close', 'retry', 'open-symbol'])

const detailContainer = computed(() => (props.mobile ? ElDrawer : SectionPanel))
const containerProps = computed(() => (
  props.mobile
    ? { modelValue: props.visible, direction: 'btt', size: '100%' }
    : { variant: 'flush' }
))
</script>

<style scoped>
.us-sector-detail__head,
.us-sector-detail__head-actions,
.us-sector-detail__row {
  display: flex;
  align-items: center;
}

.us-sector-detail__head {
  justify-content: space-between;
  gap: var(--spacing-4);
}

.us-sector-detail__head-actions {
  gap: var(--spacing-2);
}

.us-sector-detail.el-drawer :deep(.el-drawer__body) {
  padding: 0;
}

.us-sector-detail.el-drawer .us-sector-detail__head {
  flex: 1;
  min-width: 0;
}

.us-sector-detail:not(.el-drawer) :deep(.section-panel__header) {
  display: none;
}

.us-sector-detail:not(.el-drawer) :deep(.section-panel__body) {
  padding: 0;
}

.us-sector-detail:not(.el-drawer) .us-sector-detail__head--inner {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-subtle);
}

.us-sector-detail:not(.el-drawer) :deep(.status-state) {
  padding-inline: var(--spacing-4);
}

.us-sector-detail__title {
  margin: 0;
  overflow: hidden;
  color: var(--text-primary);
  font-size: var(--font-size-base);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.us-sector-detail__facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-bottom: 1px solid var(--border-subtle);
}

.us-sector-detail__fact {
  display: grid;
  align-content: center;
  gap: var(--spacing-1);
  min-width: 0;
  min-height: 56px;
  padding: var(--spacing-2) var(--spacing-3);
  border-right: 1px solid var(--border-subtle);
}

.us-sector-detail__fact:last-child {
  border-right: 0;
}

.us-sector-detail__fact-label {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.us-sector-detail__fact strong {
  overflow-wrap: anywhere;
  color: var(--text-primary);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
  line-height: 1.25;
}

.us-sector-detail__list {
  display: grid;
  padding: 0 var(--spacing-4);
}

.us-sector-detail__row {
  justify-content: space-between;
  gap: var(--spacing-4);
  min-height: 56px;
  padding: 0;
  border: 0;
  border-bottom: 1px solid var(--border-subtle);
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.us-sector-detail__row:hover {
  background: var(--state-hover);
}

.us-sector-detail__row:last-of-type {
  border-bottom: 0;
}

.us-sector-detail__total {
  margin: 0;
  padding: var(--spacing-3) 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

@media (max-width: 767px) {
  .us-sector-detail__facts {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .us-sector-detail__fact {
    min-height: 52px;
  }
}
</style>
