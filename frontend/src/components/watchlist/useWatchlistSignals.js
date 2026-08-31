import { computed, ref, watch } from 'vue'
import { getKlineData } from '@/api/stock'
import { runWithConcurrency } from '@/composables/useConcurrentRequests'
import { analyzeStockSignals, summarizeSignalResults } from '@/utils/stockSignals'

const SCAN_CONCURRENCY = 3
const KLINE_DAYS = 90

export function useWatchlistSignals(activeGroupId, activeStocks, quoteRows) {
  const results = ref([])
  const scanning = ref(false)
  const completed = ref(0)
  const lastScannedAt = ref(null)
  let requestId = 0

  const signature = computed(() => `${activeGroupId.value}|${activeStocks.value.map(({ code }) => code).join('|')}`)
  const summary = computed(() => summarizeSignalResults(results.value))
  const progress = computed(() => results.value.length
    ? Math.round(completed.value / results.value.length * 100)
    : 0)

  watch(signature, reset)

  async function scan() {
    const stocks = activeStocks.value.map(({ code, name }) => ({ code, name }))
    const currentRequest = ++requestId
    if (!stocks.length) return reset()

    scanning.value = true
    completed.value = 0
    results.value = stocks.map((stock) => ({ ...stock, status: 'loading', analysis: null }))

    await runWithConcurrency(
      stocks,
      (stock) => getKlineData(stock.code, 'daily', KLINE_DAYS),
      SCAN_CONCURRENCY,
      (settled, index, stock) => settleResult(currentRequest, settled, index, stock),
    )

    if (currentRequest !== requestId) return
    scanning.value = false
    lastScannedAt.value = Date.now()
  }

  function settleResult(currentRequest, settled, index, stock) {
    if (currentRequest !== requestId) return
    const quote = quoteRows.value.find(({ code }) => code === stock.code)
    results.value[index] = settled.status === 'fulfilled'
      ? { ...stock, status: 'success', analysis: analyzeStockSignals(settled.value, { costReturn: quote?.costReturn }) }
      : { ...stock, status: 'error', analysis: null }
    completed.value += 1
  }

  function reset() {
    requestId += 1
    results.value = []
    scanning.value = false
    completed.value = 0
    lastScannedAt.value = null
  }

  return { results, scanning, completed, lastScannedAt, summary, progress, scan }
}
