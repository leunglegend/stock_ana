<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="watchlist-snapshot__header">
        <div>
          <h3 class="watchlist-snapshot__title">自选待处理</h3>
        </div>
        <span v-if="loggedIn && fetchedAt" class="watchlist-snapshot__time">更新于 {{ fetchTime }}</span>
      </div>
    </template>

    <StatusState
      v-if="!loggedIn"
      state="empty"
      title="登录后查看自选快照"
      description="数据将从 SQLite 用户自选分组读取。"
      :min-height="220"
    >
      <template #action>
        <el-button type="primary" @click="$emit('login')">去登录</el-button>
      </template>
    </StatusState>

    <StatusState
      v-else-if="loading && items.length === 0"
      state="loading"
      title="正在加载自选行情"
      description="逐只请求个股接口，保持原始顺序。"
      :min-height="220"
    />

    <StatusState
      v-else-if="items.length === 0"
      state="empty"
      title="暂无自选股票"
      description="添加关注后，这里最多展示 5 只股票的最新行情。"
      :min-height="220"
    />

    <div v-else class="watchlist-snapshot__list">
      <article v-for="item in items" :key="item.code" class="watchlist-snapshot__monitor-row">
        <div>
          <p class="watchlist-snapshot__name">{{ item.name }}</p>
          <p class="watchlist-snapshot__code">{{ item.code }}</p>
        </div>

        <div v-if="item.status === 'success'" class="watchlist-snapshot__price">
          <PriceDisplay
            :price="item.price"
            :change="item.changeAmount"
            :change-percent="item.changePercent"
            size="sm"
          />
        </div>

        <div v-else-if="item.status === 'error'" class="watchlist-snapshot__error">
          <span>行情获取失败</span>
          <el-button link type="primary" @click="$emit('retry-stock', item.code)">重试</el-button>
        </div>

        <div v-else class="watchlist-snapshot__pending">加载中</div>

        <el-button link type="primary" @click="$emit('open-stock', item.code)">详情</el-button>
      </article>
    </div>
  </SectionPanel>
</template>

<script setup>
import { computed } from 'vue'

import PriceDisplay from '../base/PriceDisplay.vue'
import SectionPanel from '../base/SectionPanel.vue'
import StatusState from '../base/StatusState.vue'
import { formatFetchTime } from '../../utils/format'

const props = defineProps({
  loggedIn: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  fetchedAt: {
    type: [Number, String, Date],
    default: null,
  },
  items: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['login', 'retry-stock', 'open-stock'])

const fetchTime = computed(() => formatFetchTime(props.fetchedAt))
</script>

<style scoped>
.watchlist-snapshot__header,
.watchlist-snapshot__monitor-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
}

.watchlist-snapshot__code,
.watchlist-snapshot__time,
.watchlist-snapshot__pending {
  margin: 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.watchlist-snapshot__title,
.watchlist-snapshot__name {
  margin: 0;
  color: var(--text-primary);
}

.watchlist-snapshot__list { display: grid; }

.watchlist-snapshot__monitor-row {
  min-height: 58px;
  padding: var(--spacing-2) var(--spacing-3);
  border-bottom: 1px solid var(--border-subtle);
}

.watchlist-snapshot__monitor-row:hover { background: var(--state-hover); }

.watchlist-snapshot__name {
  margin-top: 0;
  font-weight: 600;
}

.watchlist-snapshot__code {
  margin-top: var(--spacing-1);
  font-family: var(--font-family-mono);
}

.watchlist-snapshot__error {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

@media (max-width: 767px) {
  .watchlist-snapshot__monitor-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .watchlist-snapshot__row > :last-child {
    grid-column: 1 / -1;
    justify-self: start;
  }
}
</style>
