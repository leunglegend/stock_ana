<template>
  <div class="us-market-page workbench-page">
    <header class="us-market-page__header workbench-page__header">
      <div class="us-market-page__heading">
        <h1 data-page-title class="us-market-page__title">美股复盘</h1>
        <p v-if="summaryData && summaryData.as_of" class="us-market-page__meta">
          美东 {{ summaryData.as_of }} 收盘
        </p>
      </div>
      <el-button :icon="Refresh" :loading="refreshing" aria-label="刷新美股复盘数据" @click="refreshAll">
        刷新
      </el-button>
    </header>

    <SectionPanel variant="flush" class="us-market-page__summary" aria-label="美股收盘摘要">
      <StatusState
        v-if="summaryError && !summaryData"
        state="error"
        title="美股摘要加载失败"
        description="当前无法读取美股收盘概览，可重新尝试。"
        :min-height="120"
        @retry="runSummary"
      />
      <StatusState
        v-else-if="summaryPending"
        state="loading"
        title="正在加载美股摘要"
        :min-height="120"
      />
      <UsIndexStrip v-else :summary="summaryData || {}" :loading="summaryLoading" />
    </SectionPanel>

    <UsAiBand
      class="us-market-page__ai"
      :text="aiText"
      :loading="aiLoading"
      :error="aiError"
      @refresh="generateAiSummary"
    />

    <UsSectorToolbar
      v-model:keyword="keyword"
      v-model:sort-key="sortKey"
      v-model:page="page"
      :page-size="pageSize"
      :total="filteredSectors.length"
    />

    <section class="us-market-page__workspace workbench-grid workbench-grid--primary">
      <div class="us-market-page__list">
        <UsSectorTable
          class="us-market-page__sectors"
          :sectors="paginatedSectors"
          :loading="sectorsLoading"
          :error="sectorsError"
          :selected-name="selected ? selected.name : ''"
          @select="selectSector"
          @retry="runSectors"
        />
      </div>
      <UsSectorDetailPanel
        :visible="!!selected"
        :loading="stocksLoading"
        :error="stocksError"
        :mobile="!isDesktop"
        :board="selected"
        :stocks="stocksData"
        @close="closeSector"
        @retry="retryStocks"
        @open-symbol="openSymbol"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'

import { getUsSectorStocks } from '@/api/us'
import SectionPanel from '@/components/base/SectionPanel.vue'
import StatusState from '@/components/base/StatusState.vue'
import UsAiBand from '@/components/us/UsAiBand.vue'
import UsIndexStrip from '@/components/us/UsIndexStrip.vue'
import UsSectorDetailPanel from '@/components/us/UsSectorDetailPanel.vue'
import UsSectorTable from '@/components/us/UsSectorTable.vue'
import UsSectorToolbar from '@/components/us/UsSectorToolbar.vue'
import { useUsBoardList } from '@/composables/useUsBoardList'
import { useAsyncSection } from '@/composables/useAsyncSection'
import { useResponsive } from '@/composables/useResponsive'
import { useUsMarket } from '@/composables/useUsMarket'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useResponsive()

// 收盘复盘数据当日不变：只手动刷新，不做轮询
const { summarySection, sectorsSection, aiText, aiLoading, aiError, generateAiSummary, closeAiSource } = useUsMarket()

const summaryData = summarySection.data
const summaryLoading = summarySection.isLoading
const summaryError = summarySection.isError
const summaryPending = computed(() => summarySection.isIdle.value || summaryLoading.value)

const sectorsData = sectorsSection.data
const sectorsLoading = sectorsSection.isLoading
const sectorsError = sectorsSection.isError
const { keyword, sortKey, page, pageSize, filteredSectors, paginatedSectors } = useUsBoardList(sectorsData)

const selected = ref(null)
// 闭包带参 fetcher：仅在 selectSector 时 run（useAsyncSection 内置 requestId 防串号）
const stocksSection = useAsyncSection(() => getUsSectorStocks(selected.value.name), { initialData: [] })
const stocksData = stocksSection.data
const stocksLoading = stocksSection.isLoading
const stocksError = stocksSection.isError

const refreshing = ref(false)

async function runSection(section) {
  try {
    await section.run()
  } catch {}
}

async function runSummary() {
  await runSection(summarySection)
}

async function runSectors() {
  await runSection(sectorsSection)
}

async function retryStocks() {
  if (!selected.value) return
  await runSection(stocksSection)
}

async function refreshAll() {
  refreshing.value = true
  try {
    const tasks = [runSection(summarySection), runSection(sectorsSection)]
    // 已展开某个板块下钻时，其成分列表也随刷新一起更新，避免详情面板停留在旧数据
    if (selected.value) tasks.push(runSection(stocksSection))
    generateAiSummary()
    await Promise.all(tasks)
  } finally {
    refreshing.value = false
  }
}

async function selectSector(sector, syncQuery = true) {
  selected.value = sector
  if (syncQuery) {
    await router.replace({ query: { ...route.query, sector: sector.name } })
  }
  await runSection(stocksSection)
}

async function closeSector(syncQuery = true) {
  stocksSection.reset()
  selected.value = null
  if (syncQuery) {
    await router.replace('/us')
  }
}

async function syncSectorFromRoute() {
  const name = typeof route.query.sector === 'string' ? route.query.sector : ''
  if (!name) {
    if (selected.value) await closeSector(false)
    return
  }
  if (selected.value?.name === name) return
  const sector = (sectorsData.value || []).find((item) => item.name === name)
  if (!sector) return
  await selectSector(sector, false)
}

function openSymbol(symbol) {
  // Global Constraint 7：本阶段不跳转个股详情，二期开放
  console.info('二期开放美股个股详情', symbol)
}

watch(
  () => route.query.sector,
  async () => {
    await syncSectorFromRoute()
  },
)

onMounted(async () => {
  await refreshAll()
  await syncSectorFromRoute()
})

onUnmounted(() => closeAiSource())
</script>

<style scoped>
/* 竖向节奏与板块行一致（header→摘要→表 用 spacing-3），避免堆叠处过密 */
.us-market-page.workbench-page { gap: var(--spacing-3); }

.us-market-page__header { min-width: 0; }
.us-market-page__heading { display: grid; gap: 2px; min-width: 0; }
.us-market-page__title { margin: 0; color: var(--text-primary); font-size: var(--font-size-2xl); line-height: 1.2; }
.us-market-page__meta { margin: 0; color: var(--text-tertiary); font-size: var(--font-size-xs); }

.us-market-page__summary { min-width: 0; }
.us-market-page__ai { min-width: 0; }

.us-market-page__workspace {
  grid-template-columns: minmax(0, 58fr) minmax(0, 42fr);
  gap: 0;
  overflow: hidden;
  background: var(--surface-panel);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-panel);
}

.us-market-page__workspace > :deep(.us-sector-detail),
.us-market-page__sectors { min-width: 0; border: 0; border-radius: 0; }

.us-market-page__list {
  display: grid;
  min-width: 0;
  border-right: 1px solid var(--border-default);
}

@media (max-width: 1023px) {
  .us-market-page__workspace {
    grid-template-columns: minmax(0, 1fr);
    overflow: visible;
    background: transparent;
    border: 0;
    border-radius: 0;
  }

  .us-market-page__list {
    border: 1px solid var(--border-default);
    border-radius: var(--radius-panel);
    overflow: hidden;
  }
}
</style>
