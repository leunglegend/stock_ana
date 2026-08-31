import { computed, ref, watch } from 'vue'
import { getStockInfo } from '@/api/stock'
import { runWithConcurrency } from '@/composables/useConcurrentRequests'
import { safeNumber } from '@/utils/format'

export function useWatchlistRows(activeGroupId, activeStocks) {
  const keyword = ref('')
  const movementFilter = ref('all')
  const sortBy = ref('manual')
  const onlyCost = ref(false)
  const quoteRows = ref([])
  const quotesLoading = ref(false)
  let quoteRequestId = 0
  const rowRequestVersions = createRowRequestVersionGate()

  const codeSignature = computed(() => activeStocks.value.map((stock) => stock.code).join('|'))
  const metaSignature = computed(() => activeStocks.value.map((stock) => `${stock.code}:${stock.cost || 0}:${stock.remark || ''}`).join('|'))
  const errorCount = computed(() => quoteRows.value.filter((row) => row.quoteStatus === 'error').length)
  const lastUpdatedAt = computed(() => {
    const timestamps = quoteRows.value.map((row) => row.updatedAt).filter(Boolean)
    return timestamps.length ? Math.max(...timestamps) : null
  })
  const filteredRows = computed(() => filterAndSortRows(quoteRows.value, {
    keyword: keyword.value,
    movement: movementFilter.value,
    onlyCost: onlyCost.value,
    sortBy: sortBy.value,
  }))

  watch(() => `${activeGroupId.value}|${codeSignature.value}`, loadQuotes, { immediate: true })
  watch(metaSignature, syncRowMeta)

  async function loadQuotes() {
    const requestId = ++quoteRequestId
    const stocks = activeStocks.value.map(normalizeStock)
    if (!stocks.length) {
      quoteRows.value = []
      quotesLoading.value = false
      return
    }
    quotesLoading.value = true
    quoteRows.value = stocks.map(createLoadingRow)
    await runWithConcurrency(stocks, (stock) => getStockInfo(stock.code), 4, (settled, _index, stock) => {
      if (requestId !== quoteRequestId) return
      const liveStock = getCurrentStock(activeStocks.value, stock.code, stock.orderIndex)
      const previous = quoteRows.value.find((row) => row.code === stock.code)
      patchRowByCode(quoteRows, stock.code, settled.status === 'fulfilled' ? createSuccessRow(liveStock, settled.value) : createErrorRow(liveStock, previous))
    })
    if (requestId === quoteRequestId) quotesLoading.value = false
  }

  async function retryQuote(code) {
    const current = quoteRows.value.find((row) => row.code === code)
    if (!current) return
    const requestId = quoteRequestId
    const rowRequestVersion = rowRequestVersions.start(code)
    patchRowByCode(quoteRows, code, createLoadingRow(getCurrentStock(activeStocks.value, code, current.orderIndex)))
    try {
      const quote = await getStockInfo(code)
      if (requestId !== quoteRequestId || !rowRequestVersions.isCurrent(code, rowRequestVersion)) return
      patchRowByCode(quoteRows, code, createSuccessRow(getCurrentStock(activeStocks.value, code, current.orderIndex), quote))
    } catch {
      if (requestId !== quoteRequestId || !rowRequestVersions.isCurrent(code, rowRequestVersion)) return
      patchRowByCode(quoteRows, code, createErrorRow(getCurrentStock(activeStocks.value, code, current.orderIndex), current))
    }
  }

  function syncRowMeta() {
    const current = new Map(activeStocks.value.map((stock, index) => [stock.code, normalizeStock(stock, index)]))
    quoteRows.value = quoteRows.value.filter((row) => current.has(row.code)).map((row) => withDerived({ ...row, ...current.get(row.code) }))
  }

  function patchRow(code, patch) {
    const current = quoteRows.value.find((row) => row.code === code)
    if (!current) return
    patchRowByCode(quoteRows, code, withDerived({ ...current, ...patch }))
  }

  function clearFilters() {
    keyword.value = ''
    movementFilter.value = 'all'
    sortBy.value = 'manual'
    onlyCost.value = false
  }

  return {
    quoteRows,
    keyword,
    movementFilter,
    sortBy,
    onlyCost,
    filteredRows,
    quotesLoading,
    errorCount,
    lastUpdatedAt,
    retryQuote,
    refreshQuotes: loadQuotes,
    patchRow,
    clearFilters,
  }
}

export function createRowRequestVersionGate() {
  const versions = new Map()
  return {
    start(code) {
      const version = (versions.get(code) || 0) + 1
      versions.set(code, version)
      return version
    },
    isCurrent(code, version) {
      return versions.get(code) === version
    },
  }
}

function normalizeStock(stock, orderIndex) {
  return {
    code: stock.code,
    name: stock.name,
    cost: safeNumber(stock.cost, 0) ?? 0,
    remark: stock.remark || '',
    orderIndex,
  }
}

function getCurrentStock(activeStocks, code, fallbackOrder = 0) {
  const index = activeStocks.findIndex((item) => item.code === code)
  return index >= 0 ? normalizeStock(activeStocks[index], index) : { code, name: code, cost: 0, remark: '', orderIndex: fallbackOrder }
}

function withDerived(row) {
  const hasCost = row.cost > 0
  const hasQuote = row.price != null
  const perSharePnL = hasCost && hasQuote ? Number((row.price - row.cost).toFixed(2)) : null
  const costReturn = hasCost && hasQuote ? (row.price - row.cost) / row.cost : null
  return { ...row, hasCost, perSharePnL, costReturn }
}

function resolveMovement(changePct, changeAmount) {
  const signal = safeNumber(changePct, safeNumber(changeAmount, 0))
  if (signal > 0) return 'up'
  if (signal < 0) return 'down'
  return 'flat'
}

function createLoadingRow(stock) {
  return withDerived({ ...stock, quoteStatus: 'loading', movement: 'loading', price: null, changeAmount: null, changePct: null, updatedAt: null })
}

function createErrorRow(stock, previous = null) {
  return withDerived({
    ...stock,
    quoteStatus: 'error',
    movement: 'error',
    price: null,
    changeAmount: null,
    changePct: null,
    updatedAt: previous?.updatedAt || null,
  })
}

function createSuccessRow(stock, quote) {
  return withDerived({
    ...stock,
    quoteStatus: 'success',
    movement: resolveMovement(quote.change_pct, quote.change_amount),
    price: safeNumber(quote.price),
    changeAmount: safeNumber(quote.change_amount),
    changePct: safeNumber(quote.change_pct),
    updatedAt: Date.now(),
  })
}

function patchRowByCode(rowsRef, code, nextRow) {
  const index = rowsRef.value.findIndex((row) => row.code === code)
  if (index >= 0) rowsRef.value[index] = nextRow
}

function filterAndSortRows(rows, filters) {
  return rows
    .filter((row) => matchesKeyword(row, filters.keyword))
    .filter((row) => matchesMovement(row, filters.movement))
    .filter((row) => !filters.onlyCost || row.hasCost)
    .slice()
    .sort((left, right) => sortRows(left, right, filters.sortBy))
}

function matchesKeyword(row, keyword) {
  const query = keyword.trim().toLowerCase()
  return !query || row.name.toLowerCase().includes(query) || row.code.toLowerCase().includes(query)
}

function matchesMovement(row, movement) {
  if (movement === 'all') return true
  return movement === 'error' ? row.quoteStatus === 'error' : row.movement === movement
}

function sortRows(left, right, sortBy) {
  const fallback = left.orderIndex - right.orderIndex
  switch (sortBy) {
    case 'change-desc': return compareNullable(right.changePct, left.changePct) || fallback
    case 'change-asc': return compareNullable(left.changePct, right.changePct) || fallback
    case 'return-desc': return compareNullable(right.costReturn, left.costReturn) || fallback
    case 'return-asc': return compareNullable(left.costReturn, right.costReturn) || fallback
    case 'name-asc': return left.name.localeCompare(right.name, 'zh-Hans-CN') || fallback
    case 'code-asc': return left.code.localeCompare(right.code, 'en-US') || fallback
    default: return fallback
  }
}

function compareNullable(left, right) {
  if (left == null && right == null) return 0
  if (left == null) return 1
  if (right == null) return -1
  return left - right
}
