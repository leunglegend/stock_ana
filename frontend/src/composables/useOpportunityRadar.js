import { computed, onMounted, reactive, ref, watch } from 'vue'
import { getBoardConcept, getBoardIndustry, getBoardStocks } from '@/api/stock'
import { useResponsive } from '@/composables/useResponsive'
import { buildRadarSummary, createRequestGate, createTimedCache, filterAndSortBoards, normalizeRadarError, oldestTimestamp, paginateRows, resolveValidPage, sortBoardStocks } from '@/utils/opportunityRadar'

const CACHE_TTL_MS = 60_000
const BOARD_PAGE_SIZE = 10
const STOCK_PAGE_SIZE = 20
const MOBILE_STOCK_PAGE_SIZE = 10
const BOARD_TYPES = Object.freeze(['industry', 'concept'])
const BOARD_LOADERS = Object.freeze({ industry: getBoardIndustry, concept: getBoardConcept })

function createBoardRecord() {
  return { data: [], loading: false, refreshing: false, error: null, selectedName: '', updatedAt: null, pending: null }
}

function createStockState() {
  return { key: '', data: [], loading: false, refreshing: false, error: null, updatedAt: null, pending: null }
}

function normalizeBoardType(type) { return type === 'concept' ? 'concept' : 'industry' }
function createSelectionKey(type, boardName) { return boardName ? `${type}:${boardName}` : '' }
function createBoardsCacheKey(type) { return `boards:${type}` }
function createStocksCacheKey(type, boardName) { return `stocks:${type}:${boardName}` }

function applyCachedBoards(record, cached) {
  record.data = Array.isArray(cached?.data) ? cached.data : []
  record.updatedAt = cached?.updatedAt ?? null
  record.error = null
  record.loading = false
  record.refreshing = false
}

function applyCachedStocks(stockState, selectionKey, cached) {
  stockState.key = selectionKey
  stockState.data = sortBoardStocks(cached?.data || [])
  stockState.updatedAt = cached?.updatedAt ?? null
  stockState.error = null
  stockState.loading = false
  stockState.refreshing = false
}

function pickVisibleBoard(boards, selectedName) {
  if (!boards.length) return null
  return boards.find((board) => board.name === selectedName) || boards[0]
}

export function useOpportunityRadar() {
  const { isDesktop } = useResponsive()
  const activeType = ref('industry')
  const keyword = ref('')
  const onlyRising = ref(false)
  const boardPage = ref(1)
  const stockPage = ref(1)
  const boardCache = createTimedCache(CACHE_TTL_MS)
  const stockCache = createTimedCache(CACHE_TTL_MS)
  const requestGate = createRequestGate()
  const boardRecords = reactive({ industry: createBoardRecord(), concept: createBoardRecord() })
  const stockState = reactive(createStockState())
  const activeRecord = computed(() => boardRecords[normalizeBoardType(activeType.value)])
  const activeBoards = computed(() => filterAndSortBoards(activeRecord.value.data))
  const filteredBoards = computed(() => filterAndSortBoards(activeRecord.value.data, { keyword: keyword.value, onlyRising: onlyRising.value }))
  const selectedBoard = computed(() => filteredBoards.value.find((board) => board.name === activeRecord.value.selectedName) || null)
  const selectedBoardKey = computed(() => createSelectionKey(activeType.value, selectedBoard.value?.name || ''))
  const visibleStockUpdatedAt = computed(() => (stockState.key === selectedBoardKey.value ? stockState.updatedAt : null))
  const stockPageSize = computed(() => isDesktop.value ? STOCK_PAGE_SIZE : MOBILE_STOCK_PAGE_SIZE)
  const paginatedStocks = computed(() => paginateRows(stockState.data, stockPage.value, stockPageSize.value))
  const stockTotal = computed(() => stockState.data.length)
  const radarSummary = computed(() => buildRadarSummary(activeBoards.value, stockTotal.value))
  const boardsLoading = computed(() => activeRecord.value.loading)
  const boardsRefreshing = computed(() => activeRecord.value.refreshing)
  const boardsError = computed(() => activeRecord.value.error)
  const stocksLoading = computed(() => stockState.loading)
  const stocksRefreshing = computed(() => stockState.refreshing)
  const stocksError = computed(() => stockState.error)
  const lastUpdatedAt = computed(() => oldestTimestamp(activeRecord.value.updatedAt, visibleStockUpdatedAt.value))

  function clearVisibleStocks() {
    requestGate.invalidate('stocks')
    stockState.key = ''
    stockState.data = []
    stockState.loading = false
    stockState.refreshing = false
    stockState.error = null
    stockState.updatedAt = null
  }
  function syncVisibleSelection() {
    const nextBoard = pickVisibleBoard(filteredBoards.value, activeRecord.value.selectedName)
    if (!nextBoard) return
    if (activeRecord.value.selectedName === nextBoard.name) return
    activeRecord.value.selectedName = nextBoard.name
  }

  async function loadBoards(type, options = {}) {
    const nextType = normalizeBoardType(type)
    const record = boardRecords[nextType]
    const cacheKey = createBoardsCacheKey(nextType)
    if (!options.force && record.pending) return record.pending
    const cached = options.force ? undefined : boardCache.get(cacheKey)
    if (cached) {
      applyCachedBoards(record, cached)
      return cached.data
    }
    const pending = requestBoards(nextType, options)
    record.pending = pending
    try {
      return await pending
    } finally {
      if (record.pending === pending) record.pending = null
    }
  }
  async function requestBoards(type, options) {
    const record = boardRecords[type]
    const channel = `boards:${type}`
    const token = requestGate.next(channel)
    const keepPreviousData = record.data.length > 0
    record.loading = !keepPreviousData
    record.refreshing = keepPreviousData
    record.error = null
    try {
      const payload = await BOARD_LOADERS[type]()
      const settled = { data: Array.isArray(payload) ? payload : [], updatedAt: Date.now() }
      boardCache.set(createBoardsCacheKey(type), settled)
      if (!requestGate.isCurrent(channel, token)) return settled.data
      record.data = settled.data
      record.updatedAt = settled.updatedAt
      record.error = null
      return settled.data
    } catch (error) {
      if (!requestGate.isCurrent(channel, token)) throw error
      record.error = normalizeRadarError(error)
      if (!keepPreviousData && !options.preserveData) record.data = []
      throw error
    } finally {
      if (!requestGate.isCurrent(channel, token)) return
      record.loading = false
      record.refreshing = false
    }
  }
  async function loadStocks(type, board, options = {}) {
    const nextType = normalizeBoardType(type)
    const boardName = board?.name || ''
    const selectionKey = createSelectionKey(nextType, boardName)
    if (!selectionKey) {
      clearVisibleStocks()
      return []
    }
    if (!options.force && stockState.pending && stockState.key === selectionKey) {
      return stockState.pending
    }
    const cacheKey = createStocksCacheKey(nextType, boardName)
    const cached = options.force ? undefined : stockCache.get(cacheKey)
    if (cached) {
      requestGate.invalidate('stocks')
      stockState.pending = null
      applyCachedStocks(stockState, selectionKey, cached)
      return stockState.data
    }
    const pending = requestStocks(nextType, boardName, selectionKey, options)
    stockState.pending = pending
    try {
      return await pending
    } finally {
      if (stockState.pending === pending) stockState.pending = null
    }
  }
  async function requestStocks(type, boardName, selectionKey, options) {
    const token = requestGate.next('stocks')
    const keepPreviousData = stockState.key === selectionKey && stockState.data.length > 0
    stockState.key = selectionKey
    stockState.loading = !keepPreviousData
    stockState.refreshing = Boolean(options.force && keepPreviousData)
    stockState.error = null
    if (!keepPreviousData) stockState.data = []
    try {
      const payload = await getBoardStocks(type, boardName)
      const settled = { data: sortBoardStocks(Array.isArray(payload) ? payload : []), updatedAt: Date.now() }
      stockCache.set(createStocksCacheKey(type, boardName), settled)
      if (!requestGate.isCurrent('stocks', token)) return settled.data
      stockState.key = selectionKey
      stockState.data = settled.data
      stockState.updatedAt = settled.updatedAt
      stockState.error = null
      return settled.data
    } catch (error) {
      if (!requestGate.isCurrent('stocks', token)) throw error
      stockState.error = normalizeRadarError(error)
      if (!keepPreviousData && !options.preserveData) stockState.data = []
      throw error
    } finally {
      if (!requestGate.isCurrent('stocks', token)) return
      stockState.loading = false
      stockState.refreshing = false
    }
  }
  async function selectType(type) {
    activeType.value = normalizeBoardType(type)
    boardPage.value = 1
    try { await loadBoards(activeType.value) } catch {}
  }
  function selectBoard(board) {
    const boardName = board?.name || ''
    if (!boardName || activeRecord.value.selectedName === boardName) return
    activeRecord.value.selectedName = boardName
  }

  async function refresh() {
    const tasks = [loadBoards(activeType.value, { force: true, preserveData: true })]
    if (selectedBoard.value) {
      tasks.push(loadStocks(activeType.value, selectedBoard.value, { force: true, preserveData: true }))
    }
    return Promise.allSettled(tasks)
  }
  async function retryBoards() {
    try { return await loadBoards(activeType.value, { force: true, preserveData: true }) } catch { return [] }
  }
  async function retryStocks() {
    if (!selectedBoard.value) return []
    try { return await loadStocks(activeType.value, selectedBoard.value, { force: true, preserveData: true }) } catch { return [] }
  }

  watch([activeType, keyword, onlyRising], () => { boardPage.value = 1 })
  watch(filteredBoards, (boards) => {
    boardPage.value = resolveValidPage(boardPage.value, boards.length, BOARD_PAGE_SIZE)
  }, { immediate: true })
  watch([stockTotal, stockPageSize], ([total, pageSize]) => {
    stockPage.value = resolveValidPage(stockPage.value, total, pageSize)
  }, { immediate: true })
  watch([activeType, filteredBoards], syncVisibleSelection, { immediate: true })
  watch(selectedBoardKey, (nextKey) => {
    stockPage.value = 1
    if (!nextKey) return clearVisibleStocks()
    void loadStocks(activeType.value, selectedBoard.value).catch(() => {})
  }, { immediate: true })
  onMounted(() => { void Promise.allSettled(BOARD_TYPES.map((type) => loadBoards(type))) })
  return {
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
  }
}
