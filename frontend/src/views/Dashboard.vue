<template>
  <div class="dashboard-page workbench-page">
    <header class="dashboard-page__header workbench-page__header">
      <div class="dashboard-page__header-title">
        <h1 data-page-title class="dashboard-page__title">市场概览</h1>
        <span class="dashboard-page__header-meta">{{ marketPulseTime }} 更新</span>
      </div>
      <div class="dashboard-page__header-actions">
        <el-button plain @click="loadSummary">刷新</el-button>
        <el-button type="primary" @click="router.push('/board')">板块全景</el-button>
      </div>
    </header>

    <StatusState
      v-if="summaryError && !summaryData"
      state="error"
      title="市场数据加载失败"
      description="当前无法读取大盘概览，请稍后重试。"
      :min-height="240"
      @retry="loadSummary"
    />

    <template v-else>
      <StatusState
        v-if="summaryLoading && !summaryData"
        state="loading"
        title="正在拉取市场概览"
        description="读取指数、涨跌家数和两市成交额。"
        :min-height="240"
      />
      <SectionPanel v-else class="dashboard-page__market-pulse" variant="flush">
        <div class="dashboard-page__pulse-content">
          <MarketIndices :summary="summaryData || {}" />
          <MarketBreadth :summary="summaryData || {}" />
        </div>
      </SectionPanel>
    </template>

    <section class="dashboard-page__workspace">
      <TopBoards :boards="topBoardsData" :loading="topBoardsLoading" :error="topBoardsError" @retry="loadBoards" @select="openBoard" @view-all="router.push('/board')" />
      <aside class="dashboard-page__inspector">
        <WatchlistSnapshot :logged-in="userStore.isLoggedIn" :loading="watchlistLoading" :items="watchlistRows" :fetched-at="watchlistFetchedAt" @login="openLogin" @retry-stock="retryWatchStock" @open-stock="openStock" />
        <MarketBreadthFacts :summary="marketBreadthData" />
      </aside>
    </section>

    <MarketAiSummary class="dashboard-page__ai-band" :text="aiSummary" :loading="aiLoading" :error="aiError" @refresh="generateAiSummary" />

    <UsSnapshotCard
      class="dashboard-page__us-card"
      :summary="cardData"
      :loading="cardLoading"
      :error="cardError"
      @retry="retryCard"
      @open="router.push('/us')"
      @sector="(name) => router.push({ path: '/us', query: { sector: name } })"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import StatusState from '@/components/base/StatusState.vue'
import SectionPanel from '@/components/base/SectionPanel.vue'
import MarketAiSummary from '@/components/dashboard/MarketAiSummary.vue'
import MarketBreadth from '@/components/dashboard/MarketBreadth.vue'
import MarketBreadthFacts from '@/components/dashboard/MarketBreadthFacts.vue'
import MarketIndices from '@/components/dashboard/MarketIndices.vue'
import TopBoards from '@/components/dashboard/TopBoards.vue'
import UsSnapshotCard from '@/components/dashboard/UsSnapshotCard.vue'
import WatchlistSnapshot from '@/components/dashboard/WatchlistSnapshot.vue'
import { useDashboardMarket } from '@/composables/useDashboardMarket'
import { useUsCard } from '@/composables/useUsCard'

const router = useRouter()
const {
  userStore,
  summaryData,
  summaryLoading,
  summaryError,
  topBoardsData,
  topBoardsLoading,
  topBoardsError,
  marketBreadthData,
  marketPulseTime,
  watchlistFetchedAt,
  watchlistLoading,
  watchlistRows,
  aiSummary,
  aiLoading,
  aiError,
  loadSummary,
  loadBoards,
  retryWatchStock,
  generateAiSummary,
} = useDashboardMarket()

// 美股收盘卡片：仅读取当日美股收盘快照，不做轮询，进入工作台时拉取一次
const { cardData, cardLoading, cardError, loadCard, retryCard } = useUsCard()

async function loadUsCard() {
  try {
    await loadCard()
  } catch {}
}

onMounted(loadUsCard)

function openLogin() { window.dispatchEvent(new CustomEvent('show-login')) }
function openBoard(board) { router.push({ path: '/board', query: { type: 'industry', name: board.name } }) }
function openStock(code) { router.push(`/stock/${code}`) }
</script>

<style scoped>
.dashboard-page.workbench-page { gap: 0; }

.dashboard-page__header {
  min-height: 44px;
  padding: 0 var(--spacing-3);
}

.dashboard-page__header-title,
.dashboard-page__header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.dashboard-page__title { margin: 0; color: var(--text-primary); font-size: var(--font-size-2xl); line-height: 1.2; }
.dashboard-page__header-meta { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.dashboard-page__header-actions :deep(.el-button) { min-height: 30px; }

.dashboard-page__market-pulse {
  border: 1px solid var(--border-default);
  border-bottom: 0;
}

.dashboard-page__pulse-content {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.dashboard-page__pulse-content :deep(.market-indices__grid),
.dashboard-page__pulse-content :deep(.market-breadth),
.dashboard-page__pulse-content :deep(.market-breadth__grid) { display: contents; }
.dashboard-page__pulse-content :deep(.market-breadth__header) { display: none; }

.dashboard-page__pulse-content :deep(.market-indices__item),
.dashboard-page__pulse-content :deep(.metric-cell) {
  min-width: 0;
  min-height: 88px;
  padding: var(--spacing-3);
  border: 0;
  border-right: 1px solid var(--border-subtle);
}

.dashboard-page__pulse-content :deep(.metric-cell:nth-child(3n + 1)) { border-left: 0; }
.dashboard-page__pulse-content :deep(.metric-cell__label),
.dashboard-page__pulse-content :deep(.market-indices__name) { font-size: var(--font-size-xs); }
.dashboard-page__pulse-content :deep(.metric-cell__value) { font-family: var(--font-family-mono); font-size: var(--font-size-3xl); font-weight: 700; }
.dashboard-page__pulse-content :deep(.price-display) { display: grid; gap: var(--spacing-1); }
.dashboard-page__pulse-content :deep(.price-display__price) { font-family: var(--font-family-mono); font-size: var(--font-size-2xl); font-weight: 700; }
.dashboard-page__pulse-content :deep(.price-display__change) { font-family: var(--font-family-mono); font-size: var(--font-size-xs); }
.dashboard-page__pulse-content > :last-child :deep(.metric-cell:last-child) { border-right: 0; }

.dashboard-page__workspace {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  min-width: 0;
  border: 1px solid var(--border-default);
  border-top: 0;
}

.dashboard-page__workspace > :deep(.section-panel) { border: 0; border-radius: 0; }
.dashboard-page__inspector{display:grid;grid-template-rows:minmax(0,1fr) auto;min-width:0;border-left:1px solid var(--border-default)}
.dashboard-page__inspector :deep(.section-panel){border:0;border-radius:0}.dashboard-page__inspector :deep(.market-breadth-facts){border-top:1px solid var(--border-subtle)}
.dashboard-page__ai-band { border-inline: 0; }
.dashboard-page__us-card { border-top: 0; }

@media (max-width: 767px) {
  .dashboard-page__header { align-items: center; }
  .dashboard-page__header-actions :deep(.el-button:first-child) { display: none; }
  .dashboard-page__pulse-content { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-page__pulse-content :deep(.market-indices__item),
  .dashboard-page__pulse-content :deep(.metric-cell) { min-height: 76px; border-bottom: 1px solid var(--border-subtle); }
  .dashboard-page__pulse-content :deep(.market-indices__item:nth-child(2n)),
  .dashboard-page__pulse-content :deep(.metric-cell:nth-child(2n + 1)) { border-right: 0; }
  .dashboard-page__workspace { grid-template-columns: minmax(0, 1fr); }
  .dashboard-page__inspector { display: none; }
}
</style>
