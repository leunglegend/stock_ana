import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import { getBoardIndustry, getMarketAiSummary, getMarketSummary, getStockInfo } from '@/api/stock'
import { runWithConcurrency } from '@/composables/useConcurrentRequests'
import { useAsyncSection } from '@/composables/useAsyncSection'
import { useWatchlistStore } from '@/store'
import { useUserStore } from '@/store/user'
import { formatFetchTime } from '@/utils/format'

const MARKET_REFRESH_INTERVAL = 30_000

function getWatchlistSeeds(groups) {
  const seen = new Set()
  const rows = []

  groups.forEach((group) => group.stocks.forEach((stock) => {
    if (seen.has(stock.code) || rows.length >= 5) return
    seen.add(stock.code)
    rows.push({ code: stock.code, name: stock.name })
  }))

  return rows
}

function createMarketSections() {
  const summarySection = useAsyncSection(getMarketSummary)
  const boardsSection = useAsyncSection(getBoardIndustry, { initialData: [] })
  const summaryFetchedAt = ref(null)

  async function loadSummary() {
    try {
      await summarySection.run()
      summaryFetchedAt.value = Date.now()
    } catch {}
  }

  async function loadBoards() {
    try {
      await boardsSection.run()
    } catch {}
  }

  return {
    summaryData: computed(() => summarySection.data.value),
    summaryLoading: computed(() => summarySection.isLoading.value),
    summaryError: computed(() => summarySection.isError.value),
    topBoardsData: computed(() => (boardsSection.data.value || []).slice(0, 9)),
    marketBreadthData: computed(() => buildMarketBreadth(summarySection.data.value, boardsSection.data.value)),
    topBoardsLoading: computed(() => boardsSection.isLoading.value),
    topBoardsError: computed(() => boardsSection.isError.value),
    marketPulseTime: computed(() => formatFetchTime(summaryFetchedAt.value)),
    loadSummary,
    loadBoards,
  }
}

function buildMarketBreadth(summary, boards = []) {
  const changes = boards.map((board) => Number(board.change_pct)).filter(Number.isFinite).sort((left, right) => left - right)
  const middle = Math.floor(changes.length / 2)
  const median = changes.length % 2 ? changes[middle] : (changes[middle - 1] + changes[middle]) / 2
  return {
    ...(summary || {}),
    strong_board_count: boards.filter((board) => Number(board.change_pct) >= 3).length,
    median_board_change: Number.isFinite(median) ? median : null,
  }
}

function createWatchlistSnapshot(userStore, watchlistStore) {
  const watchlistRows = ref([])
  const watchlistLoading = ref(false)
  const watchlistFetchedAt = ref(null)
  const watchlistSeeds = computed(() => getWatchlistSeeds(watchlistStore.groups))
  const watchlistSeedKey = computed(() => watchlistSeeds.value.map((item) => item.code).join(','))
  const watchStockRetryIds = new Map()
  let watchlistRequestId = 0

  async function loadWatchlistSnapshot() {
    const requestId = ++watchlistRequestId
    const seeds = watchlistSeeds.value

    if (!userStore.isLoggedIn || seeds.length === 0) {
      resetWatchlistSnapshot()
      return
    }

    watchlistLoading.value = true
    watchlistFetchedAt.value = null
    watchlistRows.value = seeds.map((item) => ({ ...item, status: 'loading' }))
    await runWithConcurrency(seeds, (item) => getStockInfo(item.code), 4, (settled, _index, item) => {
      updateSettledWatchRow(requestId, settled, item)
    })
    if (requestId !== watchlistRequestId) return
    watchlistLoading.value = false
    watchlistFetchedAt.value = Date.now()
  }

  function resetWatchlistSnapshot() {
    watchlistRequestId += 1
    watchlistRows.value = []
    watchlistLoading.value = false
    watchlistFetchedAt.value = null
  }

  function updateSettledWatchRow(requestId, settled, item) {
    if (requestId !== watchlistRequestId) return
    const index = watchlistRows.value.findIndex((row) => row.code === item.code)
    if (index < 0) return
    watchlistRows.value[index] = settled.status === 'fulfilled'
      ? toWatchRow(item, settled.value)
      : { ...item, status: 'error' }
  }

  async function retryWatchStock(code) {
    if (!userStore.isLoggedIn) return
    const snapshotRequestId = watchlistRequestId
    const retryRequestId = (watchStockRetryIds.get(code) || 0) + 1
    const index = watchlistRows.value.findIndex((item) => item.code === code)
    if (index < 0) return

    watchStockRetryIds.set(code, retryRequestId)
    watchlistRows.value[index] = { ...watchlistRows.value[index], status: 'loading' }
    try {
      const stock = await getStockInfo(code)
      updateRetriedWatchRow(code, snapshotRequestId, retryRequestId, stock)
    } catch {
      updateRetriedWatchRow(code, snapshotRequestId, retryRequestId)
    }
  }

  function updateRetriedWatchRow(code, snapshotRequestId, retryRequestId, stock) {
    if (!isCurrentWatchRetry(code, snapshotRequestId, retryRequestId)) return
    const index = watchlistRows.value.findIndex((item) => item.code === code)
    if (index < 0) return
    watchlistRows.value[index] = stock
      ? toWatchRow(watchlistRows.value[index], stock)
      : { ...watchlistRows.value[index], status: 'error' }
  }

  function isCurrentWatchRetry(code, snapshotRequestId, retryRequestId) {
    return snapshotRequestId === watchlistRequestId && watchStockRetryIds.get(code) === retryRequestId
  }

  return {
    watchlistRows,
    watchlistLoading,
    watchlistFetchedAt,
    watchlistSeedKey,
    loadWatchlistSnapshot,
    resetWatchlistSnapshot,
    retryWatchStock,
  }
}

function toWatchRow(item, stock) {
  return {
    ...item,
    status: 'success',
    price: stock.price,
    changeAmount: stock.change_amount,
    changePercent: stock.change_pct,
  }
}

function createAiSummary() {
  const aiSummary = ref('')
  const aiLoading = ref(false)
  const aiError = ref(false)
  let aiSource = null
  let aiRequestId = 0

  function closeAiSource() {
    if (!aiSource) return
    aiSource.close()
    aiSource = null
  }

  function generateAiSummary() {
    if (aiLoading.value) return
    const requestId = ++aiRequestId
    aiLoading.value = true
    aiError.value = false
    aiSummary.value = ''
    closeAiSource()
    aiSource = getMarketAiSummary(
      (chunk) => applyAiChunk(requestId, chunk),
      () => finishAiRequest(requestId),
      () => finishAiRequest(requestId, true)
    )
  }

  function applyAiChunk(requestId, chunk) {
    if (requestId !== aiRequestId || chunk.startsWith('📊') || chunk.startsWith('🤖')) return
    if (chunk.startsWith('❌')) return void (aiError.value = true)
    aiSummary.value += chunk
  }

  function finishAiRequest(requestId, failed = false) {
    if (requestId !== aiRequestId) return
    aiLoading.value = false
    if (failed) aiError.value = true
    aiSource = null
  }

  return { aiSummary, aiLoading, aiError, generateAiSummary, closeAiSource, cancelAiRequest: () => { aiRequestId += 1 } }
}

export function useDashboardMarket() {
  const userStore = useUserStore()
  const watchlistStore = useWatchlistStore()
  const market = createMarketSections()
  const snapshot = createWatchlistSnapshot(userStore, watchlistStore)
  const ai = createAiSummary()
  let marketRefreshTimer = null

  function startMarketRefresh() {
    if (marketRefreshTimer) return
    marketRefreshTimer = window.setInterval(() => {
      market.loadSummary()
      market.loadBoards()
    }, MARKET_REFRESH_INTERVAL)
  }

  function stopMarketRefresh() {
    if (!marketRefreshTimer) return
    window.clearInterval(marketRefreshTimer)
    marketRefreshTimer = null
  }

  watch([() => userStore.isLoggedIn, snapshot.watchlistSeedKey], ([loggedIn]) => {
    if (!loggedIn) return snapshot.resetWatchlistSnapshot()
    snapshot.loadWatchlistSnapshot()
  }, { immediate: true })

  onMounted(() => {
    market.loadSummary()
    market.loadBoards()
    startMarketRefresh()
  })

  onUnmounted(() => {
    snapshot.resetWatchlistSnapshot()
    ai.cancelAiRequest()
    stopMarketRefresh()
    ai.closeAiSource()
  })

  return { userStore, ...market, ...snapshot, ...ai }
}
