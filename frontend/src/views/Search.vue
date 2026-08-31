<template>
  <div class="search-page workbench-page">
    <header class="search-page__header workbench-page__header">
      <div class="search-page__recent-line">
        <h1 data-page-title class="search-page__title">搜索个股</h1>
        <div v-if="recentKeywords.length > 0" class="search-page__recent" aria-label="最近搜索">
          <span class="search-page__recent-label">最近</span>
          <button v-for="item in recentKeywords" :key="item" class="search-page__recent-tag" type="button" @click="applyRecentKeyword(item)">
            {{ item }}
          </button>
          <el-button class="search-page__clear-recent" link type="primary" @click="clearRecentKeywords">清除</el-button>
        </div>
      </div>
    </header>

    <section class="search-page__input-strip" aria-label="股票搜索">
      <el-input v-model="keyword" clearable aria-label="搜索股票代码或名称" placeholder="输入代码或名称" @input="handleKeywordInput" @keyup.enter="submitSearch" />
      <el-button type="primary" @click="submitSearch">搜索</el-button>
    </section>

    <section v-if="results.length" class="search-page__result-toolbar" aria-label="搜索结果控制">
      <span class="search-page__result-count">{{ results.length }} 条结果</span>
      <el-select v-model="resultSort" size="small" aria-label="搜索结果排序">
        <el-option label="默认排序" value="default" />
        <el-option label="名称 A-Z" value="name" />
        <el-option label="代码升序" value="code" />
      </el-select>
      <div v-if="results.length > pageSize" class="search-page__pagination-row">
        <el-pagination
          class="search-page__pagination"
          background
          :small="!isMobile"
          :layout="paginationLayout"
          :total="results.length"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="currentPage = $event"
        />
        <span v-if="isMobile" class="search-page__page-status" aria-live="polite">第 {{ currentPage }} / {{ pageCount }} 页</span>
      </div>
    </section>

    <SearchResults :items="paginatedResults" :state="viewState" :title="resultTitle" @open-stock="openStock" @add-stock="prepareAddStock" @retry-quote="retryQuote" @retry-search="submitSearch" />

    <GroupPicker
      :visible="pickerVisible"
      :model-value="selectedGroupId"
      :groups="watchlistStore.groupNames"
      @close="pickerVisible = false"
      @update:model-value="selectedGroupId = $event"
      @confirm="confirmAddStock"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getStockInfo, searchStock } from '@/api/stock'
import SearchResults from '@/components/stock/SearchResults.vue'
import GroupPicker from '@/components/watchlist/GroupPicker.vue'
import { runWithConcurrency } from '@/composables/useConcurrentRequests'
import { useResponsive } from '@/composables/useResponsive'
import { useWatchlistStore } from '@/store'
import { useUserStore } from '@/store/user'

const RECENT_KEY = 'stock_search_recent'
const route = useRoute()
const router = useRouter()
const watchlistStore = useWatchlistStore()
const userStore = useUserStore()
const { isMobile } = useResponsive()
const keyword = ref('')
const viewState = ref('idle')
const results = ref([])
const recentKeywords = ref(loadRecentKeywords())
const pickerVisible = ref(false)
const selectedGroupId = ref('')
const pendingStock = ref(null)
const resultSort = ref('default')
const resultTitle = computed(() => keyword.value.trim() ? `搜索结果：${keyword.value.trim()}` : '搜索结果')
const currentPage = ref(1)
const pageSize = 10
const paginationLayout = computed(() => isMobile.value ? 'prev, next' : 'total, prev, pager, next')
const pageCount = computed(() => Math.max(1, Math.ceil(results.value.length / pageSize)))
const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedResults.value.slice(start, start + pageSize)
})
const sortedResults = computed(() => {
  if (resultSort.value === 'default') return results.value
  const field = resultSort.value === 'name' ? 'name' : 'code'
  return [...results.value].sort((left, right) => String(left[field] || '').localeCompare(String(right[field] || ''), 'zh-CN'))
})
let searchRequestId = 0
let inputTimer = null

function loadRecentKeywords() {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]') } catch { return [] }
}

function saveRecentKeyword(query) {
  const next = [query, ...recentKeywords.value.filter((item) => item !== query)].slice(0, 8)
  recentKeywords.value = next
  localStorage.setItem(RECENT_KEY, JSON.stringify(next))
}

function clearRecentKeywords() {
  recentKeywords.value = []
  localStorage.removeItem(RECENT_KEY)
}

function clearInputTimer() {
  if (!inputTimer) return
  window.clearTimeout(inputTimer)
  inputTimer = null
}

function applyRecentKeyword(value) {
  keyword.value = value
  submitSearch()
}

function handleKeywordInput() {
  clearInputTimer()
  inputTimer = window.setTimeout(() => submitSearch(), 220)
}

function syncRouteQuery(query) {
  router.replace({ path: '/search', query: query ? { q: query } : {} })
}

function updateResultByCode(code, patch) {
  const index = results.value.findIndex((item) => item.code === code)
  if (index < 0) return false
  results.value[index] = { ...results.value[index], ...patch }
  return true
}

async function submitSearch() {
  const query = keyword.value.trim()
  const requestId = ++searchRequestId
  currentPage.value = 1
  results.value = []
  syncRouteQuery(query)
  if (!query) {
    viewState.value = 'idle'
    return
  }

  viewState.value = 'loading'
  try {
    const hits = await searchStock(query)
    if (requestId !== searchRequestId) return
    const topHits = hits.slice(0, 20)
    results.value = hits.map((item, index) => ({ ...item, quoteStatus: index < 20 ? 'loading' : 'idle' }))
    viewState.value = hits.length === 0 ? 'empty' : 'success'
    await runWithConcurrency(topHits, (item) => getStockInfo(item.code), 4, (settled, index, item) => {
      if (requestId !== searchRequestId || results.value[index]?.code !== item.code) return
      results.value[index] = settled.status === 'fulfilled'
        ? { ...results.value[index], quoteStatus: 'success', price: settled.value.price, changeAmount: settled.value.change_amount, changePercent: settled.value.change_pct }
        : { ...results.value[index], quoteStatus: 'error' }
    })
    if (requestId === searchRequestId) saveRecentKeyword(query)
  } catch {
    if (requestId !== searchRequestId) return
    results.value = []
    viewState.value = 'error'
  }
}

async function retryQuote(code) {
  const requestId = searchRequestId
  if (!updateResultByCode(code, { quoteStatus: 'loading' })) return
  try {
    const stock = await getStockInfo(code)
    if (requestId !== searchRequestId) return
    updateResultByCode(code, { quoteStatus: 'success', price: stock.price, changeAmount: stock.change_amount, changePercent: stock.change_pct })
  } catch {
    if (requestId !== searchRequestId) return
    updateResultByCode(code, { quoteStatus: 'error' })
  }
}

function openStock(code) { router.push(`/stock/${code}`) }

function prepareAddStock(stock) {
  if (!userStore.isLoggedIn) return void userStore.requestLogin(route.fullPath)
  pendingStock.value = stock
  selectedGroupId.value = watchlistStore.activeGroup || watchlistStore.groupNames[0]?.id || ''
  pickerVisible.value = true
}

async function confirmAddStock(groupId) {
  if (!pendingStock.value) return
  const result = await watchlistStore.addStockToGroup(groupId, pendingStock.value)
  if (result.success) ElMessage.success(`已将「${pendingStock.value.name}」加入「${result.groupName}」`)
  else if (result.reason === 'duplicate') ElMessage.warning(`「${pendingStock.value.name}」已在「${result.groupName}」中`)
  else ElMessage.error('加入自选失败')
  pickerVisible.value = false
  pendingStock.value = null
}

watch(() => route.query.q, (query) => {
  const value = typeof query === 'string' ? query : ''
  if (value === keyword.value) return
  keyword.value = value
  if (value) submitSearch()
  else {
    searchRequestId += 1
    results.value = []
    viewState.value = 'idle'
    currentPage.value = 1
  }
})

watch(resultSort, () => { currentPage.value = 1 })

onMounted(() => {
  const initialQuery = typeof route.query.q === 'string' ? route.query.q : ''
  keyword.value = initialQuery
  if (initialQuery) submitSearch()
})

onUnmounted(() => clearInputTimer())
</script>

<style scoped>
.search-page { gap: 0; background: var(--surface-primary); border: 1px solid var(--border-default); }
.search-page__header { min-height: 44px; padding: 0 var(--spacing-3); }
.search-page__recent-line, .search-page__recent, .search-page__input-strip, .search-page__result-toolbar { display: flex; align-items: center; min-width: 0; }
.search-page__recent-line { flex: 1; gap: var(--spacing-3); }
.search-page__recent { gap: var(--spacing-2); min-width: 0; overflow: hidden; }
.search-page__recent-label, .search-page__result-count { color: var(--text-secondary); font-size: var(--font-size-sm); white-space: nowrap; }
.search-page__input-strip { min-height: 48px; gap: 6px; padding: 7px var(--spacing-2); border-bottom: 1px solid var(--border-subtle); }
.search-page__input-strip :deep(.el-input) { min-width: 0; flex: 1; }
.search-page__input-strip :deep(.el-input__wrapper) { min-height: 34px; border-radius: var(--radius-control); }
.search-page__input-strip :deep(.el-button) { min-width: 68px; min-height: 34px; }
.search-page__result-toolbar { min-height: 40px; gap: var(--spacing-2); padding: 4px var(--spacing-2); border-bottom: 1px solid var(--border-subtle); }
.search-page__result-count { margin-right: auto; font-variant-numeric: tabular-nums; }
.search-page__recent-tag {
  max-width: 132px; min-height: 28px; padding: 0 var(--spacing-2); overflow: hidden; border: 0; border-radius: 0;
  background: transparent; color: var(--text-link); cursor: pointer; text-overflow: ellipsis; white-space: nowrap;
}
.search-page__recent-tag:hover, .search-page__recent-tag:focus-visible { background: var(--surface-secondary); }
.search-page__clear-recent { min-height: 28px; }

@media (max-width: 767px) {
  .search-page { border-inline: 0; }
  .search-page__header { padding-inline: var(--spacing-3); }
  .search-page__recent-line { align-items: flex-start; flex-direction: column; gap: var(--spacing-1); padding-block: var(--spacing-2); }
  .search-page__recent { width: 100%; overflow-x: auto; scrollbar-width: none; }
  .search-page__recent::-webkit-scrollbar { display: none; }
  .search-page__result-toolbar { flex-wrap: wrap; }
  .search-page__result-count { flex: 1 0 100%; }
  .search-page__pagination-row { display: flex; align-items: center; justify-content: center; gap: var(--spacing-3); max-width: 100%; }
  .search-page__page-status { color: var(--text-secondary); font-size: var(--font-size-sm); white-space: nowrap; }
  .search-page__input-strip :deep(.el-input__wrapper), .search-page__input-strip :deep(.el-button) { min-height: 44px; }
  .search-page__recent-tag { min-height: 36px; }
  .search-page__clear-recent { min-width: 44px; min-height: 44px; }
  .search-page__pagination :deep(.btn-prev),
  .search-page__pagination :deep(.btn-next) {
    min-width: 44px;
    min-height: 44px;
  }
}
</style>
