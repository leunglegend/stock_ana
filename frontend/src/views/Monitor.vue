<template>
  <main class="monitor-page workbench-page">
    <MonitorHeader
      :groups="groups"
      :active-group-id="groupId"
      :loading="loading"
      :as-of="overview?.as_of"
      :stale="isStale || error"
      :refresh-error="error"
      @update:group-id="changeGroup"
      @refresh="loadOverview"
    />
    <StatusState v-if="loading && !overview" state="loading" />
    <StatusState v-else-if="error && !overview" state="error" description="盘中监控暂时无法加载。" @retry="loadOverview" />
    <StatusState v-else-if="overview && !items.length" state="empty" title="暂无自选股" description="添加自选股后，盘中监控会按规则聚合行情和信号。">
      <template #action><el-button type="primary" plain @click="router.push('/watchlist')">管理自选股</el-button></template>
    </StatusState>
    <template v-else>
      <p v-if="error || overview?.errors?.length" class="monitor-page__notice" role="status" aria-live="polite">
        {{ error ? '本次刷新失败，当前显示上次成功数据。' : '部分聚合数据暂不可用，已保留可用结果。' }}
        <span v-if="overview?.errors?.[0]?.message">{{ overview.errors[0].message }}</span>
      </p>
      <MonitorMarketPulse :market="overview?.market" :summary="overview?.summary" />
      <section class="monitor-page__workspace">
        <div class="monitor-page__matrix">
          <MonitorTable :items="filteredItems" :selected-code="selectedCode" :filters="filters" :retrying-code="retryingCode" @select="selectCode" @open-stock="openStock" @retry="retryItem" />
          <MonitorActionQueue :items="overview?.action_queue || []" @open-stock="openStock" />
        </div>
        <MonitorInspector
          v-if="!isMobile"
          :item="selectedItem"
          :financial="financial"
          :financial-state="financialState"
          :ai-advice="aiAdvice"
          :ai-state="aiState"
          :ai-error-message="aiErrorMessage"
          @open-stock="openStock"
          @start-analyze="startAnalyze"
        />
        <el-drawer v-else v-model="inspectorVisible" direction="btt" size="82%" title="股票监控详情">
          <MonitorInspector
            :item="selectedItem"
            :financial="financial"
            :financial-state="financialState"
            :ai-advice="aiAdvice"
            :ai-state="aiState"
            :ai-error-message="aiErrorMessage"
            @open-stock="openStock"
            @start-analyze="startAnalyze"
          />
        </el-drawer>
      </section>
    </template>
  </main>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { analyzeStock, getFinancialData } from '@/api/stock'
import { getMonitorOverview } from '@/api/monitor'
import { watchlistApi } from '@/api/watchlist'
import StatusState from '@/components/base/StatusState.vue'
import MonitorHeader from '@/components/monitor/MonitorHeader.vue'
import MonitorMarketPulse from '@/components/monitor/MonitorMarketPulse.vue'
import MonitorActionQueue from '@/components/monitor/MonitorActionQueue.vue'
import MonitorTable from '@/components/monitor/MonitorTable.vue'
import MonitorInspector from '@/components/monitor/MonitorInspector.vue'
import { useResponsive } from '@/composables/useResponsive'
const route = useRoute()
const router = useRouter()
const { isMobile } = useResponsive()
const overview = ref(null)
const groups = ref([])
const groupId = ref(typeof route.query.group_id === 'string' ? route.query.group_id : 'all')
const selectedCode = ref(typeof route.query.code === 'string' ? route.query.code : '')
const loading = ref(false)
const error = ref(false)
const financialState = ref('idle')
const financial = ref(null)
const aiAdvice = ref('')
const aiState = ref('idle')
const aiErrorMessage = ref('')
const inspectorVisible = ref(false)
const retryingCode = ref('')
const validStatuses = ['attention', 'strong', 'neutral', 'error']
const validMovements = ['all', 'rising', 'falling']
const validSorts = ['status', 'change', 'relative', 'signals']
const initialStatus = typeof route.query.status === 'string' && validStatuses.includes(route.query.status) ? route.query.status : 'all'
const initialMovement = typeof route.query.movement === 'string' && validMovements.includes(route.query.movement) ? route.query.movement : 'all'
const initialSort = typeof route.query.sort_by === 'string' && validSorts.includes(route.query.sort_by) ? route.query.sort_by : 'status'
const filters = reactive({ keyword: typeof route.query.keyword === 'string' ? route.query.keyword : '', status: initialStatus, movement: initialMovement, onlyActionable: route.query.only_actionable === '1', onlyCost: route.query.only_cost === '1', sortBy: initialSort })
let refreshTimer = null
let requestId = 0
let financialRequestId = 0
let aiRequestId = 0
let aiSource = null
const items = computed(() => overview.value?.items || [])
const filteredItems = computed(() => {
  const visible = items.value.filter((item) => {
    const keyword = filters.keyword.trim().toLowerCase()
    const matchesKeyword = !keyword || item.name.toLowerCase().includes(keyword) || item.code.includes(keyword)
    const matchesStatus = filters.status === 'all' || item.status === filters.status
    const matchesAction = !filters.onlyActionable || ['attention', 'error'].includes(item.status)
    const changePct = Number(item.quote?.change_pct)
    const matchesMovement = filters.movement === 'all'
      || (filters.movement === 'rising' && changePct > 0)
      || (filters.movement === 'falling' && changePct < 0)
    const matchesCost = !filters.onlyCost || Number(item.cost) > 0
    return matchesKeyword && matchesStatus && matchesAction && matchesMovement && matchesCost
  })
  const statusOrder = { attention: 0, strong: 1, neutral: 2, error: 3 }
  const numeric = (value) => Number.isFinite(Number(value)) ? Number(value) : Number.NEGATIVE_INFINITY
  return [...visible].sort((left, right) => {
    if (filters.sortBy === 'change') return numeric(right.quote?.change_pct) - numeric(left.quote?.change_pct)
    if (filters.sortBy === 'relative') return numeric(right.metrics?.relative_strength_vs_sh_pct) - numeric(left.metrics?.relative_strength_vs_sh_pct)
    if (filters.sortBy === 'signals') return right.signals.length - left.signals.length
    return (statusOrder[left.status] ?? 4) - (statusOrder[right.status] ?? 4) || left.code.localeCompare(right.code)
  })
})
const selectedItem = computed(() => items.value.find((item) => item.code === selectedCode.value) || filteredItems.value[0] || null)
const isStale = computed(() => Boolean(overview.value?.market?.stale || items.value.some((item) => item.quote?.stale)))
async function loadGroups() {
  try {
    const response = await watchlistApi.getGroups()
    groups.value = response.data || []
  } catch { groups.value = [] }
}
async function loadOverview() {
  const currentRequest = ++requestId
  loading.value = true
  error.value = false
  try {
    const result = await getMonitorOverview({ group_id: groupId.value, days: 90 })
    if (currentRequest !== requestId) return
    overview.value = result
    if (!items.value.some((item) => item.code === selectedCode.value)) selectedCode.value = filteredItems.value[0]?.code || ''
  } catch {
    if (currentRequest === requestId) error.value = true
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}
async function loadFinancial(code) {
  const currentRequest = ++financialRequestId
  if (!code) {
    financial.value = null
    financialState.value = 'idle'
    return
  }
  financialState.value = 'loading'
  try {
    const result = await getFinancialData(code)
    if (currentRequest !== financialRequestId) return
    financial.value = result
    financialState.value = result ? 'success' : 'empty'
  } catch (requestError) {
    if (currentRequest !== financialRequestId) return
    financial.value = null
    financialState.value = requestError?.response?.status === 404 ? 'empty' : 'error'
  }
}
function closeAiSource() {
  aiRequestId += 1
  if (!aiSource) return
  aiSource.close()
  aiSource = null
}
function startAnalyze() {
  const code = selectedItem.value?.code
  if (!code || aiState.value === 'loading') return
  closeAiSource()
  aiAdvice.value = ''
  aiErrorMessage.value = ''
  aiState.value = 'loading'
  const currentRequest = ++aiRequestId
  aiSource = analyzeStock(
    code,
    (chunk) => {
      if (currentRequest !== aiRequestId || chunk.startsWith('📊') || chunk.startsWith('🤖')) return
      if (chunk.startsWith('❌')) {
        aiErrorMessage.value = chunk
        aiState.value = 'error'
        return
      }
      aiAdvice.value += chunk
    },
    () => {
      if (currentRequest !== aiRequestId) return
      aiState.value = aiAdvice.value.trim() ? 'success' : 'empty'
      aiSource = null
    },
    () => {
      if (currentRequest !== aiRequestId) return
      aiState.value = aiAdvice.value.trim() ? 'success' : 'error'
      if (!aiAdvice.value) aiErrorMessage.value = 'AI 分析失败，请稍后重试'
      aiSource = null
    },
  )
}
function isTradingSession(now = new Date()) {
  const minutes = now.getHours() * 60 + now.getMinutes()
  return (minutes >= 570 && minutes < 690) || (minutes >= 780 && minutes < 900)
}
async function retryItem(code) {
  if (!code || retryingCode.value) return
  retryingCode.value = code
  selectedCode.value = code
  try {
    const result = await getMonitorOverview({ group_id: groupId.value, days: 90, code })
    const returnedItems = result?.items || []
    if (!overview.value || !returnedItems.length) return
    const byWatchlistId = new Map(returnedItems.filter((item) => item.watchlist_item_id != null).map((item) => [item.watchlist_item_id, item]))
    const byCode = new Map(returnedItems.map((item) => [item.code, item]))
    const mergedItems = (overview.value.items || []).map((item) => {
      const replacement = item.watchlist_item_id != null
        ? byWatchlistId.get(item.watchlist_item_id)
        : byCode.get(item.code)
      return replacement || item
    })
    overview.value = {
      ...overview.value,
      items: mergedItems,
      summary: summarizeItems(mergedItems, overview.value.summary),
      action_queue: mergeActionQueue(overview.value.action_queue, result.action_queue, code),
    }
  } catch {
    // 保留原有行级错误，避免单项重试失败导致整页空白。
  } finally {
    retryingCode.value = ''
  }
}
function summarizeItems(nextItems, previousSummary = {}) {
  const changes = nextItems.map((item) => Number(item.quote?.change_pct)).filter(Number.isFinite)
  const relative = nextItems.map((item) => Number(item.metrics?.relative_strength_vs_sh_pct)).filter(Number.isFinite)
  return {
    ...previousSummary,
    stock_count: nextItems.length,
    rising_count: nextItems.filter((item) => Number(item.quote?.change_pct) > 0).length,
    falling_count: nextItems.filter((item) => Number(item.quote?.change_pct) < 0).length,
    strong_count: nextItems.filter((item) => item.status === 'strong').length,
    attention_count: nextItems.filter((item) => item.status === 'attention').length,
    error_count: nextItems.filter((item) => item.status === 'error').length,
    average_change_pct: changes.length ? Number((changes.reduce((sum, value) => sum + value, 0) / changes.length).toFixed(2)) : null,
    average_relative_strength_pct: relative.length ? Number((relative.reduce((sum, value) => sum + value, 0) / relative.length).toFixed(2)) : null,
  }
}
function mergeActionQueue(currentQueue = [], retryQueue = [], code) {
  const priorityOrder = { high: 0, medium: 1 }
  return [...currentQueue.filter((item) => item.code !== code), ...(retryQueue || [])]
    .sort((left, right) => (priorityOrder[left.priority] ?? 9) - (priorityOrder[right.priority] ?? 9))
}
function changeGroup(value) {
  groupId.value = value
  selectedCode.value = ''
  router.replace({ query: { ...route.query, group_id: value, code: undefined } })
  loadOverview()
}
function selectCode(code) {
  selectedCode.value = code
  if (isMobile.value) inspectorVisible.value = true
  router.replace({ query: { ...route.query, code } })
}
async function openStock(code) {
  if (!code) return
  const preservedQuery = {
    ...route.query,
    group_id: groupId.value,
    code,
    keyword: filters.keyword || undefined,
    status: filters.status !== 'all' ? filters.status : undefined,
    movement: filters.movement !== 'all' ? filters.movement : undefined,
    only_actionable: filters.onlyActionable ? '1' : undefined,
    only_cost: filters.onlyCost ? '1' : undefined,
    sort_by: filters.sortBy !== 'status' ? filters.sortBy : undefined,
  }
  await router.replace({ query: preservedQuery })
  await router.push({
    path: `/stock/${code}`,
    query: {
      from: 'monitor',
      group_id: groupId.value,
      code,
      keyword: filters.keyword || undefined,
      status: filters.status !== 'all' ? filters.status : undefined,
      movement: filters.movement !== 'all' ? filters.movement : undefined,
      only_actionable: filters.onlyActionable ? '1' : undefined,
      only_cost: filters.onlyCost ? '1' : undefined,
      sort_by: filters.sortBy !== 'status' ? filters.sortBy : undefined,
    },
  })
}
onMounted(() => {
  loadGroups()
  loadOverview()
  refreshTimer = window.setInterval(() => {
    if (isTradingSession()) loadOverview()
  }, 60_000)
})
onBeforeUnmount(() => {
  window.clearInterval(refreshTimer)
  closeAiSource()
  financialRequestId += 1
})
watch(filters, (next) => {
  router.replace({
    query: {
      ...route.query,
      keyword: next.keyword.trim() || undefined,
      status: next.status !== 'all' ? next.status : undefined,
      movement: next.movement !== 'all' ? next.movement : undefined,
      only_actionable: next.onlyActionable ? '1' : undefined,
      only_cost: next.onlyCost ? '1' : undefined,
      sort_by: next.sortBy !== 'status' ? next.sortBy : undefined,
    },
  })
}, { deep: true })
watch(() => [route.query.group_id, route.query.code], ([nextGroup, nextCode]) => {
  const nextGroupId = typeof nextGroup === 'string' ? nextGroup : 'all'
  if (nextGroupId !== groupId.value) {
    groupId.value = nextGroupId
    loadOverview()
  }
  if (typeof nextCode === 'string' && nextCode !== selectedCode.value) selectedCode.value = nextCode
})
watch(() => selectedItem.value?.code, (code) => {
  loadFinancial(code)
  closeAiSource()
  aiAdvice.value = ''
  aiErrorMessage.value = ''
  aiState.value = 'idle'
})
watch(filteredItems, (next) => {
  if (!next.some((item) => item.code === selectedCode.value)) selectedCode.value = next[0]?.code || ''
})
</script>

<style scoped>
.monitor-page { gap: var(--spacing-3); }
.monitor-page__notice { margin: 0; padding: var(--spacing-2) var(--spacing-3); border: 1px solid var(--border-default); background: var(--surface-warning); color: var(--text-secondary); font-size: var(--font-size-xs); }
.monitor-page__workspace { display: grid; grid-template-columns: minmax(0, 1fr) 260px; min-width: 0; background: var(--surface-primary); border: 1px solid var(--border-default); }
.monitor-page__matrix { min-width: 0; }
@media (max-width: 1279px) { .monitor-page__workspace { grid-template-columns: minmax(0, 1fr); } }
</style>
