export function normalizeOptionalMetric(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

export function filterAndSortBoards(boards = [], options = {}) {
  const query = String(options.keyword || '').trim().toLowerCase()
  return boards
    .filter((board) => !query || String(board.name || '').toLowerCase().includes(query))
    .filter((board) => !options.onlyRising || normalizeOptionalMetric(board.change_pct) > 0)
    .slice()
    .sort(compareChangeDescending)
}

export function sortBoardStocks(stocks = []) {
  return stocks.slice().sort(compareChangeDescending)
}

export function paginateRows(rows = [], page = 1, pageSize = 20) {
  const start = (page - 1) * pageSize
  return rows.slice(start, start + pageSize)
}

export function resolveValidPage(page, total, pageSize) {
  const safePage = Number.isFinite(page) ? Math.floor(page) : 1
  const safeTotal = Number.isFinite(total) ? Math.max(0, Math.floor(total)) : 0
  const safePageSize = Number.isFinite(pageSize) && pageSize > 0 ? Math.floor(pageSize) : 1
  const maxPage = Math.max(1, Math.ceil(safeTotal / safePageSize))
  return Math.min(maxPage, Math.max(1, safePage))
}

export function oldestTimestamp(...timestamps) {
  const values = timestamps.filter((value) => typeof value === 'number' && Number.isFinite(value))
  return values.length ? Math.min(...values) : null
}

export function buildRadarSummary(boards = [], candidateCount = 0) {
  const rankedBoards = filterAndSortBoards(boards)
  const risingBoards = rankedBoards.filter((board) => normalizeOptionalMetric(board.change_pct) > 0)
  const strongestLeader = rankedBoards.reduce((leadingBoard, board) => (
    getLeadingChange(board) > getLeadingChange(leadingBoard) ? board : leadingBoard
  ), null)
  const total = rankedBoards.length

  return {
    strongestBoard: rankedBoards[0] || null,
    diffusionRate: total ? (risingBoards.length / total) * 100 : null,
    risingBoardCount: risingBoards.length,
    totalBoardCount: total,
    strongestLeader: strongestLeader || null,
    candidateCount: Number.isFinite(candidateCount) ? Math.max(0, candidateCount) : 0,
  }
}

export function getStockSignal(changePct) {
  const change = normalizeOptionalMetric(changePct)
  if (change == null) return '待补'
  if (change >= 3) return '强势'
  if (change > 0) return '走强'
  if (change < 0) return '承压'
  return '平衡'
}

export function readPendingRadarStock(storage) {
  const target = resolveRadarStorage(storage)
  if (!target) return null
  try {
    return sanitizePendingRadarStock(JSON.parse(target.getItem(PENDING_RADAR_STOCK_KEY) || 'null'))
  } catch {
    return null
  }
}

export function writePendingRadarStock(storage, stock) {
  const target = resolveRadarStorage(storage)
  if (!target) return
  const nextStock = sanitizePendingRadarStock(stock)
  try {
    if (!nextStock) target.removeItem(PENDING_RADAR_STOCK_KEY)
    else target.setItem(PENDING_RADAR_STOCK_KEY, JSON.stringify(nextStock))
  } catch {}
}

export function clearPendingRadarStock(storage) {
  const target = resolveRadarStorage(storage)
  if (!target) return
  try {
    target.removeItem(PENDING_RADAR_STOCK_KEY)
  } catch {}
}

export function createTimedCache(ttlMs, now = Date.now) {
  const entries = new Map()

  return {
    get(key) {
      const entry = entries.get(key)
      if (!entry) return undefined
      if (now() - entry.createdAt <= ttlMs) return entry.value
      entries.delete(key)
      return undefined
    },
    set(key, value) {
      entries.set(key, { value, createdAt: now() })
    },
    delete(key) {
      entries.delete(key)
    },
    clear() {
      entries.clear()
    },
  }
}

export function createRequestGate() {
  const generations = new Map()

  return {
    next(channel) {
      const generation = (generations.get(channel) || 0) + 1
      generations.set(channel, generation)
      return generation
    },
    isCurrent(channel, generation) {
      return generations.get(channel) === generation
    },
    invalidate(channel) {
      generations.set(channel, (generations.get(channel) || 0) + 1)
    },
  }
}

function compareChangeDescending(left, right) {
  const leftChange = normalizeOptionalMetric(left.change_pct) ?? -Infinity
  const rightChange = normalizeOptionalMetric(right.change_pct) ?? -Infinity
  return rightChange - leftChange
}

function getLeadingChange(board) {
  return normalizeOptionalMetric(board?.leading_change) ?? -Infinity
}

function resolveRadarStorage(storage) {
  if (storage) return storage
  if (typeof window === 'undefined') return null
  try {
    return window.sessionStorage || null
  } catch {
    return null
  }
}

function sanitizePendingRadarStock(stock) {
  if (!stock || typeof stock !== 'object') return null
  const code = typeof stock.code === 'string' ? stock.code.trim() : ''
  if (!code) return null
  return {
    code,
    name: typeof stock.name === 'string' ? stock.name : '',
  }
}

const PENDING_RADAR_STOCK_KEY = 'opportunity-radar:pending-stock'
