<template>
  <section class="watchlist-filters" aria-label="自选筛选">
    <div class="watchlist-filters__toolbar">
      <el-input
        id="watchlist-filter-keyword"
        class="watchlist-filters__search"
        :model-value="keyword"
        clearable
        aria-label="按股票名称或代码筛选"
        placeholder="名称 / 代码"
        @update:model-value="$emit('update:keyword', $event)"
      />

      <el-select class="watchlist-filters__select" :model-value="movement" aria-label="按涨跌状态筛选" @update:model-value="$emit('update:movement', $event)">
        <el-option v-for="item in movementOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>

      <el-select class="watchlist-filters__sort" :model-value="sortBy" aria-label="选择排序方式" @update:model-value="$emit('update:sortBy', $event)">
        <el-option v-for="item in sortOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>

      <el-checkbox :model-value="onlyCost" @update:model-value="$emit('update:onlyCost', $event)">仅看已设成本</el-checkbox>

      <span>结果 {{ total }} 条</span>
      <span>{{ loading ? '行情刷新中' : updatedAt ? `最近更新 ${formatFetchTime(updatedAt)}` : '尚未获取行情' }}</span>
      <el-button link type="primary" @click="$emit('clear')">清空筛选</el-button>
    </div>
  </section>
</template>

<script setup>
import { formatFetchTime } from '@/utils/format'

defineProps({
  keyword: { type: String, default: '' },
  movement: { type: String, default: 'all' },
  sortBy: { type: String, default: 'manual' },
  onlyCost: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
  updatedAt: { type: [Number, String, Date], default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['update:keyword', 'update:movement', 'update:sortBy', 'update:onlyCost', 'clear'])

const movementOptions = [
  { label: '全部', value: 'all' },
  { label: '上涨', value: 'up' },
  { label: '下跌', value: 'down' },
  { label: '平盘', value: 'flat' },
  { label: '加载失败', value: 'error' },
]

const sortOptions = [
  { label: '保持分组顺序', value: 'manual' },
  { label: '涨跌幅从高到低', value: 'change-desc' },
  { label: '涨跌幅从低到高', value: 'change-asc' },
  { label: '成本收益率从高到低', value: 'return-desc' },
  { label: '成本收益率从低到高', value: 'return-asc' },
  { label: '名称 A-Z', value: 'name-asc' },
  { label: '代码从小到大', value: 'code-asc' },
]
</script>

<style scoped>
.watchlist-filters {
  min-width: 0;
}
.watchlist-filters__toolbar {
  display: flex; align-items: center; flex-wrap: wrap; gap: var(--spacing-2); color: var(--text-tertiary); font-size: var(--font-size-xs);
}
.watchlist-filters__search { flex: 1 1 240px; min-width: 180px; }
.watchlist-filters__select { width: 104px; }
.watchlist-filters__sort { width: 154px; }
@media (max-width: 767px) {
  .watchlist-filters__toolbar { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .watchlist-filters__search { grid-column: 1 / -1; min-width: 0; }
  .watchlist-filters__select, .watchlist-filters__sort { width: 100%; }
  .watchlist-filters :deep(.el-input__wrapper),
  .watchlist-filters :deep(.el-select__wrapper) { min-height: 44px; }
  .watchlist-filters :deep(.el-checkbox),
  .watchlist-filters :deep(.el-button) {
    display: inline-flex;
    align-items: center;
    min-width: 44px;
    min-height: 44px;
  }
}
</style>
