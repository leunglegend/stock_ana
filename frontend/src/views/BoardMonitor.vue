<template>
  <div class="board-page workbench-page">
    <header class="board-page__header workbench-page__header">
      <h1 data-page-title class="board-page__title">板块排行</h1>
    </header>
    <section class="board-page__toolbar workbench-toolbar">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="行业板块" name="industry" />
        <el-tab-pane label="概念板块" name="concept" />
      </el-tabs>

      <div class="board-page__filters">
        <el-input v-model="keyword" clearable aria-label="按板块名称筛选" placeholder="筛选板块名称" />
        <el-select v-model="sortKey" aria-label="板块排序方式" style="width: 180px">
          <el-option label="按涨跌幅" value="change_pct" />
          <el-option label="按成交额" value="total_turnover" />
          <el-option label="按换手率" value="turnover_rate" />
          <el-option label="按上涨家数" value="rise_count" />
          <el-option label="按下跌家数" value="fall_count" />
          <el-option label="按股票数" value="stock_count" />
        </el-select>
      </div>
      <div class="board-page__pager">
        <span v-if="filteredBoards.length" class="board-page__total">共 {{ filteredBoards.length }} 个</span>
        <el-pagination
          v-if="filteredBoards.length > boardPageSize"
          v-model:current-page="boardPage"
          :page-size="boardPageSize"
          :total="filteredBoards.length"
          :pager-count="isMobile ? 3 : 5"
          background
          :layout="isMobile ? 'prev, next' : 'prev, pager, next'"
          size="small"
        />
        <span v-if="isMobile && filteredBoards.length > boardPageSize" class="board-page__page-state">
          第 {{ boardPage }} / {{ boardPageCount }} 页
        </span>
      </div>
    </section>
    <section class="board-page__workspace workbench-grid workbench-grid--primary">
      <div class="board-page__list">
        <BoardTable
          :title="activeTab === 'industry' ? '行业板块' : '概念板块'"
          :boards="paginatedBoards"
          :loading="activeSectionLoading"
          :error="activeSectionError"
          :selected-name="selectedBoard?.name"
          @select="openBoard($event, true)"
          @retry="retryActiveSection"
        />
      </div>
      <BoardDetailPanel
        :visible="detailVisible"
        :loading="detailLoading"
        :error="detailError"
        :mobile="!isDesktop"
        :board="selectedBoard"
        :board-type="selectedBoardType"
        :stocks="boardStocks"
        @close="closeBoard(true)"
        @retry="reloadBoardStocks"
        @open-stock="openStock"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getBoardConcept, getBoardIndustry, getBoardStocks } from '@/api/stock'
import BoardDetailPanel from '@/components/board/BoardDetailPanel.vue'
import BoardTable from '@/components/board/BoardTable.vue'
import { useAsyncSection } from '@/composables/useAsyncSection'
import { useResponsive } from '@/composables/useResponsive'
import { createRequestGate } from '@/utils/opportunityRadar'

const route = useRoute()
const router = useRouter()
const { isDesktop, isMobile } = useResponsive()

const activeTab = ref('industry')
const keyword = ref('')
const sortKey = ref('change_pct')
const boardPage = ref(1)
const boardPageSize = 10
const detailVisible = ref(false)
const selectedBoard = ref(null)
const selectedBoardType = ref('industry')
const boardStocks = ref([])
const detailLoading = ref(false)
const detailError = ref(false)
const syncingRoute = ref(false)
const lastSyncedRouteKey = ref('')
const detailRequestGate = createRequestGate()
let routeSyncGeneration = 0

const industrySection = useAsyncSection(getBoardIndustry, { initialData: [] })
const conceptSection = useAsyncSection(getBoardConcept, { initialData: [] })

const activeSection = computed(() => (
  activeTab.value === 'concept' ? conceptSection : industrySection
))
const activeSectionLoading = computed(() => activeSection.value.isLoading.value)
const activeSectionError = computed(() => activeSection.value.isError.value)

const filteredBoards = computed(() => {
  const source = activeSection.value.data.value || []
  const query = keyword.value.trim()
  return [...source]
    .filter((board) => !query || board.name.includes(query))
    .sort((left, right) => Number(right[sortKey.value] || 0) - Number(left[sortKey.value] || 0))
})

const paginatedBoards = computed(() => {
  const start = (boardPage.value - 1) * boardPageSize
  return filteredBoards.value.slice(start, start + boardPageSize)
})
const boardPageCount = computed(() => Math.ceil(filteredBoards.value.length / boardPageSize))

async function loadBoards(type) {
  const section = type === 'concept' ? conceptSection : industrySection
  if (section.hasLoaded.value && !section.isError.value) return
  try {
    await section.run()
  } catch {}
}

async function retryActiveSection() {
  try {
    await activeSection.value.retry()
    await syncBoardFromRoute()
  } catch {}
}

function routeKey(type, name) {
  return name ? `${type}:${name}` : `${type}:`
}

function currentRouteKey() {
  const type = route.query.type === 'concept' ? 'concept' : 'industry'
  const name = typeof route.query.name === 'string' ? route.query.name : ''
  return routeKey(type, name)
}

function isCurrentRouteSync(generation, key) {
  return generation === routeSyncGeneration && key === currentRouteKey()
}

async function handleTabChange(tabName) {
  routeSyncGeneration += 1
  activeTab.value = tabName
  boardPage.value = 1
  closeBoard(false)
  await replaceRouteQuery(tabName, '')
  await loadBoards(tabName)
}

async function openBoard(board, syncQuery) {
  routeSyncGeneration += 1
  const boardType = activeTab.value
  const boardName = board.name
  selectedBoard.value = board
  selectedBoardType.value = boardType
  detailVisible.value = true
  await reloadBoardStocks()
  if (syncQuery && selectedBoardType.value === boardType && selectedBoard.value?.name === boardName) {
    await replaceRouteQuery(boardType, boardName)
  }
}

async function reloadBoardStocks() {
  if (!selectedBoard.value) return
  const token = detailRequestGate.next('stocks')
  detailLoading.value = true
  detailError.value = false
  try {
    const stocks = await getBoardStocks(selectedBoardType.value, selectedBoard.value.name)
    if (!detailRequestGate.isCurrent('stocks', token)) return
    boardStocks.value = stocks
  } catch {
    if (!detailRequestGate.isCurrent('stocks', token)) return
    boardStocks.value = []
    detailError.value = true
  } finally {
    if (detailRequestGate.isCurrent('stocks', token)) {
      detailLoading.value = false
    }
  }
}

function closeBoard(syncQuery) {
  if (syncQuery) routeSyncGeneration += 1
  detailRequestGate.invalidate('stocks')
  detailVisible.value = false
  selectedBoard.value = null
  boardStocks.value = []
  detailError.value = false
  if (syncQuery) {
    replaceRouteQuery(activeTab.value, '')
  }
}

function openStock(code) {
  router.push(`/stock/${code}`)
}

async function replaceRouteQuery(type, name) {
  const nextKey = routeKey(type, name)
  if (lastSyncedRouteKey.value === nextKey) return
  syncingRoute.value = true
  lastSyncedRouteKey.value = nextKey
  await router.replace({ path: '/board', query: { type, ...(name ? { name } : {}) } })
  syncingRoute.value = false
}

async function syncBoardFromRoute() {
  const syncGeneration = ++routeSyncGeneration
  detailRequestGate.invalidate('stocks')
  const type = route.query.type === 'concept' ? 'concept' : 'industry'
  const name = typeof route.query.name === 'string' ? route.query.name : ''
  const syncKey = routeKey(type, name)
  lastSyncedRouteKey.value = syncKey
  activeTab.value = type
  boardPage.value = 1
  await loadBoards(type)
  if (!isCurrentRouteSync(syncGeneration, syncKey)) return
  if (!name) {
    closeBoard(false)
    return
  }
  const source = type === 'concept' ? conceptSection.data.value : industrySection.data.value
  const board = source.find((item) => item.name === name)
  if (!board) {
    closeBoard(false)
    return
  }
  const alreadyOpen = detailVisible.value
    && selectedBoardType.value === type
    && selectedBoard.value?.name === name
  if (alreadyOpen) return

  selectedBoard.value = board
  selectedBoardType.value = type
  detailVisible.value = true
  await reloadBoardStocks()
  if (!isCurrentRouteSync(syncGeneration, syncKey)) return
  }
watch(
  () => [route.query.type, route.query.name],
  async () => {
    if (syncingRoute.value) return
    await syncBoardFromRoute()
  }
)

watch([keyword, sortKey], () => {
  boardPage.value = 1
})

onMounted(async () => {
  await loadBoards('industry')
  await syncBoardFromRoute()
})
</script>

<style scoped>
.board-page.workbench-page { gap: var(--spacing-3); }
.board-page__header .board-page__title { font-size: var(--font-size-2xl); }
.board-page__title { margin: 0; color: var(--text-primary); line-height: 1.2; }
.board-page__toolbar { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--spacing-3); min-width: 0; }
.board-page__toolbar :deep(.el-tabs__header) { margin: 0; }
.board-page__filters { display: flex; align-items: center; flex-wrap: wrap; gap: var(--spacing-4); }
.board-page__workspace {
  grid-template-columns: minmax(0, 58fr) minmax(0, 42fr);
  gap: 0;
  overflow: hidden;
  background: var(--surface-panel);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-panel);
}
.board-page__workspace > :deep(.section-panel), .board-page__workspace > :deep(.board-detail), .board-page__list :deep(.section-panel) { min-width: 0; border: 0; border-radius: 0; }
.board-page__list { display: grid; min-width: 0; border-right: 1px solid var(--border-default); }
.board-page__pager { display: flex; align-items: center; justify-content: flex-end; gap: var(--spacing-2); color: var(--text-tertiary); font-size: var(--font-size-xs); }
.board-page__page-state { order: -1; }

@media (max-width: 1023px) {
  .board-page__workspace { grid-template-columns: minmax(0, 1fr); overflow: visible; background: transparent; border: 0; border-radius: 0; }
  .board-page__list { border: 1px solid var(--border-default); border-radius: var(--radius-panel); overflow: hidden; }
}

@media (max-width: 767px) {
  .board-page__toolbar { grid-template-columns: minmax(0, 1fr); align-items: stretch; }
  .board-page__filters { width: 100%; }
  .board-page__filters :deep(.el-input), .board-page__filters :deep(.el-select) { width: 100% !important; }
  .board-page__pager { justify-content: space-between; }
}
</style>
