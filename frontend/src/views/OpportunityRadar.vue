<template>
  <div class="radar-page workbench-page">
    <header class="radar-page__header workbench-page__header">
      <h1 data-page-title class="radar-page__title">机会雷达</h1>
      <div class="radar-page__header-meta" aria-live="polite">
        <span class="radar-page__meta-label">{{ activeTypeLabel }}</span>
        <span>{{ refreshLabel }}</span>
      </div>
    </header>
    <RadarToolbar
      :type="activeType"
      :keyword="keyword"
      :only-rising="onlyRising"
      :refreshing="isRefreshing"
      @update:type="selectType"
      @update:keyword="keyword = $event"
      @update:only-rising="onlyRising = $event"
      @refresh="refresh"
    />

    <section class="radar-page__summary-strip" aria-label="雷达结果摘要">
      <div class="radar-page__summary-item">
        <span class="radar-page__summary-label">强势板块</span>
        <strong class="radar-page__summary-value">{{ radarSummary.strongestBoard?.name || '--' }}</strong>
        <PercentageDisplay :value="radarSummary.strongestBoard?.change_pct" size="sm" />
      </div>
      <div class="radar-page__summary-item">
        <span class="radar-page__summary-label">扩散率</span>
        <strong class="radar-page__summary-value">{{ diffusionLabel }}</strong>
        <span class="radar-page__summary-meta">{{ radarSummary.risingBoardCount }} / {{ radarSummary.totalBoardCount }} 上涨</span>
      </div>
      <div class="radar-page__summary-item">
        <span class="radar-page__summary-label">强势领涨股</span>
        <strong class="radar-page__summary-value">{{ radarSummary.strongestLeader?.leading_stock || '--' }}</strong>
        <PercentageDisplay :value="radarSummary.strongestLeader?.leading_change" size="sm" />
      </div>
      <div class="radar-page__summary-item">
        <span class="radar-page__summary-label">当前候选</span>
        <strong class="radar-page__summary-value tabular-nums">{{ radarSummary.candidateCount }}</strong>
        <span class="radar-page__summary-meta">{{ selectedBoard?.name || '未选择板块' }}</span>
      </div>
    </section>

    <section class="radar-page__workspace" aria-label="机会雷达工作台">
      <div class="radar-page__index" aria-label="板块信号索引">
        <BoardRanking
          :type="activeType"
          :boards="filteredBoards"
          :active-boards="activeBoards"
          :selected-name="selectedBoard?.name || ''"
          :loading="boardsLoading"
          :refreshing="boardsRefreshing"
          :error="boardsError"
          :page="boardPage"
          :page-size="10"
          :total="filteredBoards.length"
          :compact="isCompact"
          @select="selectBoard"
          @retry="retryBoards"
          @page-change="boardPage = $event"
        />
      </div>

      <div ref="stocksPanelRef" class="radar-page__detail" aria-label="板块详情与成分股">
        <BoardSnapshot
          :board="selectedBoard"
          :type="activeType"
          :refreshing="stocksRefreshing"
          :updated-at="lastUpdatedAt"
        />
        <BoardStockTable
          :board="selectedBoard"
          :rows="paginatedStocks"
          :loading="stocksLoading"
          :refreshing="stocksRefreshing"
          :error="stocksError"
          :page="stockPage"
          :page-size="stockPageSize"
          :total="stockTotal"
          :mobile="isCompact"
          :compact="isCompact"
          @open-stock="openDetail"
          @add-watchlist="requestAdd"
          @retry="retryStocks"
          @page-change="stockPage = $event"
        />
      </div>
    </section>

    <GroupPicker
      :visible="pickerVisible"
      :model-value="selectedGroupId"
      :groups="watchlistGroups"
      @close="closePicker"
      @update:model-value="selectedGroupId = $event"
      @confirm="confirmAdd"
    />
  </div>
</template>
<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import BoardRanking from '@/components/radar/BoardRanking.vue'
import BoardSnapshot from '@/components/radar/BoardSnapshot.vue'
import BoardStockTable from '@/components/radar/BoardStockTable.vue'
import RadarToolbar from '@/components/radar/RadarToolbar.vue'
import PercentageDisplay from '@/components/base/PercentageDisplay.vue'
import GroupPicker from '@/components/watchlist/GroupPicker.vue'
import { useOpportunityRadar } from '@/composables/useOpportunityRadar'
import { useResponsive } from '@/composables/useResponsive'
import { useWatchlistStore } from '@/store'
import { useUserStore } from '@/store/user'
import { formatFetchTime, formatPercent } from '@/utils/format'
import { readPendingRadarStock, writePendingRadarStock, clearPendingRadarStock } from '@/utils/opportunityRadar'
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const watchlistStore = useWatchlistStore()
const { isDesktop } = useResponsive()
const isCompact = computed(() => !isDesktop.value)
const stocksPanelRef = ref(null)
const pickerVisible = ref(false)
const selectedGroupId = ref('')
const pendingStock = ref(readPendingRadarStock())
const adding = ref(false)
const emptyGroupHintShown = ref(false)
const {
  activeType,
  keyword,
  onlyRising,
  selectedBoard,
  boardPage,
  stockPage,
  stockPageSize,
  activeBoards,
  filteredBoards,
  paginatedStocks,
  stockTotal,
  radarSummary,
  boardsLoading,
  boardsRefreshing,
  boardsError,
  stocksLoading,
  stocksRefreshing,
  stocksError,
  lastUpdatedAt,
  selectType,
  selectBoard,
  refresh,
  retryBoards,
  retryStocks,
} = useOpportunityRadar()
const watchlistGroups = computed(() => watchlistStore.groupNames)
const activeTypeLabel = computed(() => activeType.value === 'concept' ? '概念板块' : '行业板块')
const isRefreshing = computed(() => boardsRefreshing.value || stocksRefreshing.value)
const diffusionLabel = computed(() => formatPercent(radarSummary.value.diffusionRate, 1, false))
const refreshLabel = computed(() => {
  if (isRefreshing.value) return '更新中'
  if (lastUpdatedAt.value) return `最近更新 ${formatFetchTime(lastUpdatedAt.value)}`
  if (boardsLoading.value) return '正在加载板块'
  return '尚未获取数据'
})
watch(selectedBoard, async (nextBoard, prevBoard) => {
  if (!isCompact.value || !nextBoard || nextBoard.name === prevBoard?.name || typeof window === 'undefined') return
  await nextTick()
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  stocksPanelRef.value?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' })
})
watch(
  [() => userStore.isLoggedIn, () => watchlistStore.loading, () => watchlistStore.cloudMode, () => watchlistStore.cloudError, () => watchlistGroups.value.length],
  () => openPendingPicker(),
  { immediate: true },
)
function resolveDefaultGroupId() {
  return watchlistStore.activeGroup || watchlistGroups.value[0]?.id || ''
}

function clearPendingStock() {
  clearPendingRadarStock()
  pendingStock.value = null
  selectedGroupId.value = ''
}
function closePicker() {
  pickerVisible.value = false
  if (!adding.value) clearPendingStock()
}

function openDetail(code) {
  router.push(`/stock/${code}`)
}
function openPendingPicker() {
  if (!pendingStock.value || pickerVisible.value || adding.value) return
  if (!userStore.isLoggedIn || watchlistStore.loading || !watchlistStore.cloudMode || watchlistStore.cloudError) return
  selectedGroupId.value = resolveDefaultGroupId()
  if (!selectedGroupId.value) {
    if (!emptyGroupHintShown.value) {
      emptyGroupHintShown.value = true
      ElMessage.warning('暂无可用分组，请先在自选页创建分组')
    }
    clearPendingStock()
    return
  }
  emptyGroupHintShown.value = false
  pickerVisible.value = true
}

function requestAdd(stock) {
  const nextStock = { code: stock.code, name: stock.name }
  writePendingRadarStock(undefined, nextStock)
  pendingStock.value = nextStock
  emptyGroupHintShown.value = false
  if (!userStore.isLoggedIn) return userStore.requestLogin(route.fullPath)
  openPendingPicker()
}
async function confirmAdd(groupId) {
  if (!pendingStock.value || adding.value) return
  adding.value = true
  try {
    const result = await watchlistStore.addStockToGroup(groupId, pendingStock.value)
    if (result.success) {
      ElMessage.success(`已加入「${result.groupName}」`)
      pickerVisible.value = false
      clearPendingStock()
      return
    }
    if (result.reason === 'duplicate') return void ElMessage.warning('该股票已在目标分组中')
    ElMessage.error('加入自选失败')
  } finally {
    adding.value = false
  }
}
</script>
<style scoped>
.radar-page { gap: var(--spacing-2); }
.radar-page__header-meta {
  display: grid;
  justify-items: end;
  gap: 4px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}
.radar-page__meta-label { color: var(--text-primary); font-weight: 600; }
.radar-page__summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--border-default);
  background: var(--surface-panel);
}
.radar-page__summary-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 4px var(--spacing-2);
  min-width: 0;
  padding: var(--spacing-2) var(--spacing-3);
  border-right: 1px solid var(--border-subtle);
}
.radar-page__summary-item:last-child { border-right: 0; }
.radar-page__summary-label,.radar-page__summary-meta { color: var(--text-tertiary); font-size: var(--font-size-xs); line-height: var(--line-height-normal); }
.radar-page__summary-label { grid-column: 1 / -1; }
.radar-page__summary-value { min-width: 0; overflow: hidden; color: var(--text-primary); font-family: var(--font-family-mono); font-size: var(--font-size-2xl); font-weight: 700; line-height: var(--line-height-tight); text-overflow: ellipsis; white-space: nowrap; }
.radar-page__summary-meta { overflow: hidden; text-align: right; text-overflow: ellipsis; white-space: nowrap; }
.radar-page__workspace {
  display: grid;
  grid-template-columns: minmax(0, 30fr) minmax(0, 70fr);
  gap: 0;
  min-width: 0;
  overflow: hidden;
  background: var(--surface-panel);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-panel);
}
.radar-page__index {
  min-width: 0;
  border-right: 1px solid var(--border-default);
}
.radar-page__index :deep(.section-panel),
.radar-page__detail :deep(.section-panel) {
  border: 0;
  border-radius: 0;
}
.radar-page__detail { display: grid; gap: 0; min-width: 0; align-content: start; }
@media (max-width: 1023px) { .radar-page__detail { grid-row: 1; } .radar-page__index { border-right: 0; border-top: 1px solid var(--border-default); } }
@media (max-width: 1279px) { .radar-page__workspace { grid-template-columns: minmax(0, 1fr); } .radar-page__detail { grid-row: 1; } .radar-page__index { border-right: 0; border-top: 1px solid var(--border-default); } }
@media (max-width: 767px) {
  .radar-page__header-meta {
    justify-items: start;
    white-space: normal;
  }
  .radar-page__summary-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .radar-page__summary-item:nth-child(2) { border-right: 0; }
  .radar-page__summary-item:nth-child(-n + 2) { border-bottom: 1px solid var(--border-subtle); }
}
</style>
