<template>
  <section class="us-sector-toolbar workbench-toolbar">
    <el-tabs model-value="industry">
      <el-tab-pane label="行业板块" name="industry" />
    </el-tabs>
    <div class="us-sector-toolbar__filters">
      <el-input :model-value="keyword" clearable aria-label="按板块名称筛选" placeholder="筛选板块名称" @update:model-value="$emit('update:keyword', $event)" />
      <el-select :model-value="sortKey" aria-label="板块排序方式" style="width: 180px" @update:model-value="$emit('update:sortKey', $event)">
        <el-option label="按涨跌幅" value="change_pct" />
        <el-option label="按上涨家数" value="advancers" />
        <el-option label="按下跌家数" value="decliners" />
        <el-option label="按股票数" value="constituent_count" />
      </el-select>
    </div>
    <div class="us-sector-toolbar__pager">
      <span v-if="total">共 {{ total }} 个</span>
      <el-pagination
        v-if="total > pageSize"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        :pager-count="isMobile ? 3 : 5"
        background
        :layout="isMobile ? 'prev, next' : 'prev, pager, next'"
        size="small"
        @update:current-page="$emit('update:page', $event)"
      />
      <span v-if="isMobile && total > pageSize" class="us-sector-toolbar__page-state">第 {{ page }} / {{ Math.ceil(total / pageSize) }} 页</span>
    </div>
  </section>
</template>

<script setup>
import { useResponsive } from '../../composables/useResponsive'
defineProps({
  keyword: { type: String, default: '' },
  sortKey: { type: String, default: 'change_pct' },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  total: { type: Number, default: 0 },
})
defineEmits(['update:keyword', 'update:sortKey', 'update:page'])
const { isMobile } = useResponsive()
</script>

<style scoped>
.us-sector-toolbar { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--spacing-3); min-width: 0; }
.us-sector-toolbar :deep(.el-tabs__header) { margin: 0; }
.us-sector-toolbar__filters { display: flex; align-items: center; flex-wrap: wrap; gap: var(--spacing-4); }
.us-sector-toolbar__pager { display: flex; align-items: center; justify-content: flex-end; gap: var(--spacing-2); color: var(--text-tertiary); font-size: var(--font-size-xs); }
.us-sector-toolbar__page-state { order: -1; }
@media (max-width: 767px) {
  .us-sector-toolbar { grid-template-columns: minmax(0, 1fr); align-items: stretch; }
  .us-sector-toolbar__filters { width: 100%; }
  .us-sector-toolbar__filters :deep(.el-input), .us-sector-toolbar__filters :deep(.el-select) { width: 100% !important; }
  .us-sector-toolbar__pager { justify-content: space-between; }
}
</style>
