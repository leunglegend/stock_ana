<template>
  <div class="stock-detail-page workbench-page">
    <StockHeader class="stock-detail-page__identity-band workbench-page__header" :name="stockInfo?.name || '--'" :code="String(code || '')" :price="stockInfo?.price" :change-amount="stockInfo?.change_amount" :change-percent="stockInfo?.change_pct" :watched="isWatched" @back="router.back()" @toggle-watch="toggleWatch" />
    <StatusState v-if="quoteLoading && !stockInfo" state="loading" title="正在读取个股行情" description="读取最新价格、涨跌幅和成交数据。" :min-height="220" />
    <StatusState v-else-if="quoteError && !stockInfo" state="error" title="个股行情加载失败" description="当前无法读取该股票，请稍后重试。" :min-height="220" @retry="loadQuote" />

    <template v-else>
      <section class="stock-detail-page__workspace">
        <section class="stock-detail-page__chart" aria-label="K 线研究区">
          <StatusState v-if="klineLoading && !klineData" state="loading" title="正在加载 K 线" :min-height="480" />
          <StatusState v-else-if="klineError && !klineData" state="error" title="K 线数据加载失败" :min-height="480" @retry="loadKline" />
          <KLineChart v-else :kline-data="klineData" :loading="klineLoading" @period-change="handlePeriodChange" />
        </section>

        <aside class="stock-detail-page__research">
          <QuoteFacts v-if="stockInfo" :stock="stockInfo" />
          <el-tabs v-model="activeTab" class="stock-detail-page__tabs" @tab-change="handleTabChange">
            <el-tab-pane label="财务" name="financial">
              <StatusState v-if="financialState === 'loading'" state="loading" title="正在读取财务字段" description="只显示财务接口返回的真实字段。" :min-height="260" />
              <StatusState v-else-if="financialState === 'error'" state="error" title="财务数据加载失败" description="当前无法读取财务数据，可重新尝试。" :min-height="260" @retry="loadFinancial" />
              <StatusState v-else-if="financialState === 'empty'" state="empty" title="暂无财务数据" description="该股票当前没有返回财务字段。" :min-height="260" />
              <FinancialCard v-else :financial="financial" :loading="false" />
            </el-tab-pane>
            <el-tab-pane label="决策报告" name="decision">
              <DecisionReport :report="decisionReport" :state="decisionState" :error-message="decisionErrorMessage" @retry="loadDecisionReport" />
            </el-tab-pane>
            <el-tab-pane label="AI 分析" name="ai">
              <AiAdvice :code="String(code || '')" :advice="aiAdvice" :state="aiState" :error-message="aiErrorMessage" @start-analyze="startAnalyze" />
            </el-tab-pane>
          </el-tabs>
        </aside>
      </section>
    </template>
    <GroupPicker :visible="pickerVisible" :model-value="selectedGroupId" :groups="watchlistStore.groupNames" @close="pickerVisible = false" @update:model-value="selectedGroupId = $event" @confirm="confirmAddToGroup" />
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { analyzeStock, getFinancialData, getKlineData, getStockDecisionReport, getStockInfo } from '@/api/stock'
import AiAdvice from '@/components/AiAdvice.vue'
import FinancialCard from '@/components/FinancialCard.vue'
import KLineChart from '@/components/KLineChart.vue'
import StatusState from '@/components/base/StatusState.vue'
import GroupPicker from '@/components/watchlist/GroupPicker.vue'
import QuoteFacts from '@/components/stock/QuoteFacts.vue'
import DecisionReport from '@/components/stock/DecisionReport.vue'
import StockHeader from '@/components/stock/StockHeader.vue'
import { useWatchlistStore } from '@/store'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const watchlistStore = useWatchlistStore()
const userStore = useUserStore()
const code = computed(() => String(route.params.code || ''))
const activeTab = ref('financial')
const stockInfo = ref(null)
const klineData = ref(null)
const financial = ref(null)
const aiAdvice = ref('')
const aiState = ref('idle')
const aiErrorMessage = ref('')
const klinePeriod = ref('daily')
const quoteLoading = ref(false)
const klineLoading = ref(false)
const quoteError = ref(false)
const klineError = ref(false)
const financialState = ref('idle')
const decisionReport = ref(null)
const decisionState = ref('idle')
const decisionErrorMessage = ref('')
const pickerVisible = ref(false)
const selectedGroupId = ref('')
let aiSource = null
let pageGeneration = 0
let aiRequestId = 0
let quoteRequestId = 0
let klineRequestId = 0
let financialRequestId = 0
let decisionRequestId = 0
let financialLoaded = false
let decisionLoaded = false
const isWatched = computed(() => watchlistStore.isWatched(code.value))

function isCurrentRequest(generation, requestId, latestId, targetCode, targetPeriod = '') {
  return generation === pageGeneration && requestId === latestId && targetCode === code.value && (!targetPeriod || targetPeriod === klinePeriod.value)
}

function isCurrentAiRequest(requestId, targetCode) {
  return requestId === aiRequestId && targetCode === code.value
}

function closeAiSource() {
  aiRequestId += 1
  if (!aiSource) return
  aiSource.close()
  aiSource = null
}

function resetPageState() {
  closeAiSource()
  stockInfo.value = null
  klineData.value = null
  financial.value = null
  aiAdvice.value = ''
  aiState.value = 'idle'
  aiErrorMessage.value = ''
  quoteLoading.value = false
  klineLoading.value = false
  quoteError.value = false
  klineError.value = false
  decisionReport.value = null
  decisionState.value = 'idle'
  decisionErrorMessage.value = ''
  financialLoaded = false
  decisionLoaded = false
  pickerVisible.value = false
}

async function loadQuote(generation = pageGeneration) {
  const requestId = ++quoteRequestId
  const targetCode = code.value
  quoteLoading.value = true
  quoteError.value = false
  try {
    const data = await getStockInfo(targetCode)
    if (!isCurrentRequest(generation, requestId, quoteRequestId, targetCode)) return
    stockInfo.value = data
  } catch {
    if (!isCurrentRequest(generation, requestId, quoteRequestId, targetCode)) return
    stockInfo.value = null
    quoteError.value = true
  } finally {
    if (isCurrentRequest(generation, requestId, quoteRequestId, targetCode)) quoteLoading.value = false
  }
}

async function loadKline(generation = pageGeneration) {
  const requestId = ++klineRequestId
  const targetCode = code.value
  const targetPeriod = klinePeriod.value
  klineLoading.value = true
  klineError.value = false
  try {
    const data = await getKlineData(targetCode, targetPeriod)
    if (!isCurrentRequest(generation, requestId, klineRequestId, targetCode, targetPeriod)) return
    klineData.value = data
  } catch {
    if (!isCurrentRequest(generation, requestId, klineRequestId, targetCode, targetPeriod)) return
    klineData.value = null
    klineError.value = true
  } finally {
    if (isCurrentRequest(generation, requestId, klineRequestId, targetCode, targetPeriod)) klineLoading.value = false
  }
}

function loadFinancial(generation = pageGeneration) {
  financialLoaded = true
  return loadFinancialRequest(generation)
}

async function loadFinancialRequest(generation = pageGeneration) {
  const requestId = ++financialRequestId
  const targetCode = code.value
  financialState.value = 'loading'
  try {
    const data = await getFinancialData(targetCode)
    if (!isCurrentRequest(generation, requestId, financialRequestId, targetCode)) return
    financial.value = data
    financialState.value = financial.value ? 'success' : 'empty'
  } catch (error) {
    if (!isCurrentRequest(generation, requestId, financialRequestId, targetCode)) return
    financial.value = null
    financialState.value = error?.response?.status === 404 ? 'empty' : 'error'
  }
}

function loadDecisionReport(generation = pageGeneration) {
  decisionLoaded = true
  return loadDecisionReportRequest(generation)
}

async function loadDecisionReportRequest(generation = pageGeneration) {
  if (!code.value) return
  const requestId = ++decisionRequestId
  const targetCode = code.value
  decisionState.value = 'loading'
  decisionErrorMessage.value = ''
  try {
    const data = await getStockDecisionReport(targetCode)
    if (!isCurrentRequest(generation, requestId, decisionRequestId, targetCode)) return
    decisionReport.value = data
    decisionState.value = data ? 'success' : 'empty'
  } catch (error) {
    if (!isCurrentRequest(generation, requestId, decisionRequestId, targetCode)) return
    decisionReport.value = null
    decisionState.value = 'error'
    decisionErrorMessage.value = error?.response?.data?.detail || '当前无法生成决策报告，请稍后重试'
  }
}
function handlePeriodChange(period) {
  if (period === klinePeriod.value) return
  klinePeriod.value = period
  if (code.value) loadKline()
}

function startAnalyze() {
  if (!code.value || aiState.value === 'loading') return
  closeAiSource()
  aiAdvice.value = ''
  aiErrorMessage.value = ''
  aiState.value = 'loading'
  const requestId = ++aiRequestId
  const targetCode = code.value
  aiSource = analyzeStock(
    targetCode,
    (chunk) => {
      if (!isCurrentAiRequest(requestId, targetCode) || chunk.startsWith('📊') || chunk.startsWith('🤖')) return
      if (chunk.startsWith('❌')) {
        aiErrorMessage.value = chunk
        aiState.value = 'error'
        return
      }
      aiAdvice.value += chunk
    },
    () => {
      if (!isCurrentAiRequest(requestId, targetCode)) return
      aiState.value = aiAdvice.value.trim() ? 'success' : 'empty'
      aiSource = null
    },
    () => {
      if (!isCurrentAiRequest(requestId, targetCode)) return
      aiState.value = aiAdvice.value.trim() ? 'success' : 'error'
      if (!aiAdvice.value) aiErrorMessage.value = 'AI 分析失败，请稍后重试'
      aiSource = null
    }
  )
}

function toggleWatch() {
  if (!stockInfo.value) return
  if (isWatched.value) {
    removeFromWatchlist()
    return
  }
  if (!userStore.isLoggedIn) {
    userStore.requestLogin(route.fullPath)
    return
  }
  selectedGroupId.value = watchlistStore.activeGroup || watchlistStore.groupNames[0]?.id || ''
  pickerVisible.value = true
}

async function removeFromWatchlist() {
  const targetCode = code.value
  const groups = watchlistStore.groups
    .filter((group) => group.stocks.some((stock) => stock.code === targetCode))
    .map((group) => ({ id: group.id, name: group.name }))
  if (!groups.length) return
  for (const group of groups) await watchlistStore.removeStock(targetCode, group.id)
  const remaining = groups.filter((group) => watchlistStore.isWatched(targetCode, group.id))
  if (remaining.length === groups.length) return ElMessage.error('移出自选失败')
  if (!remaining.length) return ElMessage.success('已移出自选')
  ElMessage.warning(`已从 ${groups.length - remaining.length} 个分组移出，仍保留在 ${remaining.length} 个分组`)
}

async function confirmAddToGroup(groupId) {
  if (!stockInfo.value) return
  const result = await watchlistStore.addStockToGroup(groupId, {
    code: stockInfo.value.code,
    name: stockInfo.value.name,
  })
  if (result.success) {
    ElMessage.success(`已将「${stockInfo.value.name}」加入「${result.groupName}」`)
  } else if (result.reason === 'duplicate') {
    ElMessage.warning(`「${stockInfo.value.name}」已在「${result.groupName}」中`)
  } else {
    ElMessage.error('加入自选失败')
  }
  pickerVisible.value = false
}

function loadPage() {
  const generation = ++pageGeneration
  resetPageState()
  const primaryRequests = [loadQuote(generation), loadKline(generation)]
  Promise.all(primaryRequests).then(() => {
    if (generation !== pageGeneration || activeTab.value !== 'financial' || financialLoaded) return
    loadFinancial(generation)
  })
}

function handleTabChange(tabName) {
  if (tabName === 'financial' && !financialLoaded) loadFinancial(pageGeneration)
  if (tabName === 'decision' && !decisionLoaded) loadDecisionReport(pageGeneration)
}

watch(code, (nextCode, prevCode) => {
  if (nextCode === prevCode) return
  if (!nextCode) return resetPageState()
  loadPage()
}, { immediate: true })

onUnmounted(() => {
  closeAiSource()
})
</script>

<style scoped>
.stock-detail-page { gap: var(--spacing-3); }
.stock-detail-page__workspace { display: grid; grid-template-columns: minmax(0, 72fr) minmax(280px, 28fr); min-width: 0; overflow: hidden; border: 1px solid var(--border-default); background: var(--surface-primary); }
.stock-detail-page__chart,.stock-detail-page__research { min-width: 0; }
.stock-detail-page__research { display: grid; align-content: start; border-left: 1px solid var(--border-default); }
.stock-detail-page__tabs :deep(.el-tabs__header) { margin: 0; padding: 0 var(--spacing-3); border-top: 1px solid var(--border-subtle); }
.stock-detail-page__tabs :deep(.el-tabs__content) { min-height: 280px; }
.stock-detail-page__tabs :deep(.el-tab-pane) { min-width: 0; }
@media (max-width: 1023px) { .stock-detail-page__workspace { grid-template-columns: minmax(0, 1fr); } .stock-detail-page__research { border-top: 1px solid var(--border-default); border-left: 0; } }
@media (max-width: 767px) { .stock-detail-page__tabs :deep(.el-tabs__content) { min-height: 320px; } .stock-detail-page__tabs :deep(.el-tabs__item) { min-height: 44px; } }
</style>
