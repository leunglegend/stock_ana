import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const dashboard = await readFile(new URL('../src/views/Dashboard.vue', import.meta.url), 'utf8')
const indices = await readFile(new URL('../src/components/dashboard/MarketIndices.vue', import.meta.url), 'utf8')
const breadth = await readFile(new URL('../src/components/dashboard/MarketBreadth.vue', import.meta.url), 'utf8')
const boards = await readFile(new URL('../src/components/dashboard/TopBoards.vue', import.meta.url), 'utf8')
const watchlist = await readFile(new URL('../src/components/dashboard/WatchlistSnapshot.vue', import.meta.url), 'utf8')
const aiSummary = await readFile(new URL('../src/components/dashboard/MarketAiSummary.vue', import.meta.url), 'utf8')
const marketComposable = await readFile(new URL('../src/composables/useDashboardMarket.js', import.meta.url), 'utf8').catch(() => '')

test('市场概览采用页头、六格脉冲、2:1 工作区和底部 AI 带', () => {
  assert.match(dashboard, /dashboard-page__header[\s\S]*dashboard-page__header-meta/)
  assert.match(dashboard, /\.dashboard-page__header\s*\{[\s\S]*min-height:\s*44px/)
  assert.match(dashboard, /<section class="dashboard-page__workspace">/)
  assert.match(dashboard, /\.dashboard-page__workspace\s*\{[\s\S]*grid-template-columns:\s*minmax\(0, 2fr\) minmax\(280px, 1fr\)/)
  assert.match(dashboard, /<MarketAiSummary class="dashboard-page__ai-band"/)
})

test('市场脉冲由六个连续指标组成，移动端切换为两列', () => {
  assert.match(dashboard, /\.dashboard-page__pulse-content\s*\{[\s\S]*grid-template-columns:\s*repeat\(6, minmax\(0, 1fr\)\)/)
  assert.match(dashboard, /@media \(max-width: 767px\)[\s\S]*dashboard-page__pulse-content[\s\S]*repeat\(2, minmax\(0, 1fr\)\)/)
  assert.match(indices, /grid-template-columns:\s*repeat\(3, minmax\(0, 1fr\)\)/)
  ;['涨跌家数', '涨停 \/ 跌停', '两市成交额'].forEach((label) => assert.match(breadth, new RegExp(`label="${label}"`)))
})

test('板块和自选以连续数据行展示，AI 不再形成独立卡片', () => {
  assert.match(boards, /<table[\s\S]*?class="top-boards__table">/)
  assert.match(boards, /height:\s*40px/)
  assert.match(watchlist, /class="watchlist-snapshot__monitor-row"/)
  assert.match(watchlist, /min-height:\s*58px/)
  assert.doesNotMatch(aiSummary, /<SectionPanel/)
  assert.match(aiSummary, /class="market-ai__band"/)
})

test('市场页保留刷新、重试和跳转行为', () => {
  assert.match(marketComposable, /const MARKET_REFRESH_INTERVAL = 30_000/)
  assert.match(marketComposable, /marketRefreshTimer = window\.setInterval/)
  assert.match(dashboard, /@retry="loadSummary"/)
  assert.match(dashboard, /@retry="loadBoards"/)
  assert.match(dashboard, /@select="openBoard"/)
  assert.match(dashboard, /@open-stock="openStock"/)
})

test('市场页面把数据编排委托给专用 composable，并保持在单文件上限内', () => {
  const lineCount = dashboard.split('\n').length

  assert.ok(lineCount <= 300, `Dashboard.vue 当前为 ${lineCount} 行`)
  assert.match(dashboard, /import \{ useDashboardMarket \} from '@\/composables\/useDashboardMarket'/)
  assert.match(dashboard, /const \{[\s\S]*loadSummary[\s\S]*generateAiSummary[\s\S]*\} = useDashboardMarket\(\)/)
  assert.doesNotMatch(dashboard, /const MARKET_REFRESH_INTERVAL = 30_000/)
  assert.doesNotMatch(dashboard, /function startMarketRefresh\(/)
  assert.match(marketComposable, /export function useDashboardMarket\(\)/)
  assert.match(marketComposable, /watchStockRetryIds/)
  assert.match(marketComposable, /closeAiSource\(\)/)
})

test('市场工作区展示九个板块，并在右侧提供真实市场宽度事实区', () => {
  assert.match(dashboard, /<MarketBreadthFacts :summary="marketBreadthData"/)
  assert.match(dashboard, /dashboard-page__inspector/)
  assert.match(dashboard, /@media \(max-width: 767px\) \{[\s\S]*\.dashboard-page__inspector \{ display: none; \}/)
  assert.match(marketComposable, /topBoardsData: computed\(\(\) => \(boardsSection\.data\.value \|\| \[\]\)\.slice\(0, 9\)\)/)
  assert.match(marketComposable, /strong_board_count/)
  assert.match(marketComposable, /median_board_change/)
})
