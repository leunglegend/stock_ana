import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const dashboard = await readFile(new URL('../src/views/Dashboard.vue', import.meta.url), 'utf8')
const dashboardMarket = await readFile(new URL('../src/composables/useDashboardMarket.js', import.meta.url), 'utf8')
const boardMonitor = await readFile(new URL('../src/views/BoardMonitor.vue', import.meta.url), 'utf8')
const indices = await readFile(new URL('../src/components/dashboard/MarketIndices.vue', import.meta.url), 'utf8')
const breadth = await readFile(new URL('../src/components/dashboard/MarketBreadth.vue', import.meta.url), 'utf8')
const topBoards = await readFile(new URL('../src/components/dashboard/TopBoards.vue', import.meta.url), 'utf8')
const watchlist = await readFile(new URL('../src/components/dashboard/WatchlistSnapshot.vue', import.meta.url), 'utf8')
const boardTable = await readFile(new URL('../src/components/board/BoardTable.vue', import.meta.url), 'utf8')

test('市场首页按脉冲、板块、自选和 AI 次级区的顺序组织', () => {
  assert.doesNotMatch(dashboard, /Research Workbench|先看市场宽度/)
  assert.match(dashboard, /dashboard-page__market-pulse/)
  assert.ok(dashboard.indexOf('<MarketIndices') < dashboard.indexOf('<MarketBreadth'))
  assert.ok(dashboard.indexOf('<MarketBreadth') < dashboard.indexOf('<TopBoards'))
  assert.ok(dashboard.indexOf('<TopBoards') < dashboard.indexOf('<WatchlistSnapshot'))
  assert.ok(dashboard.indexOf('<WatchlistSnapshot') < dashboard.indexOf('<MarketAiSummary'))
})

test('市场指标、板块和自选快照采用无行卡的连续工作面', () => {
  assert.match(dashboard, /<SectionPanel v-else class="dashboard-page__market-pulse" variant="flush">/)
  assert.match(dashboard, /grid-template-columns:\s*repeat\(6, minmax\(0, 1fr\)\)/)
  assert.match(dashboard, /dashboard-page__workspace\s*\{[\s\S]*minmax\(0, 2fr\) minmax\(280px, 1fr\)/)
  ;[topBoards, watchlist].forEach((source) => {
    assert.match(source, /<SectionPanel variant="flush">/)
    assert.doesNotMatch(source, /__eyebrow/)
  })
  ;[indices, breadth].forEach((source) => assert.doesNotMatch(source, /__eyebrow/))
  assert.doesNotMatch(indices, /market-indices__card/)
  assert.doesNotMatch(topBoards, /border-radius:/)
  assert.doesNotMatch(watchlist, /border-radius:/)
})

test('板块排行把控件收敛到工具栏，并在非桌面端保持抽屉详情', () => {
  assert.match(boardMonitor, /const \{[^}]*isDesktop[^}]*\} = useResponsive\(\)/)
  assert.match(boardMonitor, /:mobile="!isDesktop"/)
  assert.match(boardMonitor, /<section class="board-page__toolbar workbench-toolbar">[\s\S]*<el-pagination/)
  assert.match(boardTable, /<SectionPanel(?=[^>]*\bvariant="flush")[^>]*>/)
  assert.match(boardTable, /min-height: var\(--data-row-height\)/)
})

test('打开板块详情保留当前筛选和分页上下文', () => {
  const openBoard = boardMonitor.match(/async function openBoard\([\s\S]*?\n\}/)?.[0] || ''
  assert.doesNotMatch(openBoard, /boardPage\.value = 1/)
})

test('市场行情会定时刷新，重复自选重试不会被旧请求覆盖', () => {
  assert.match(dashboard, /useDashboardMarket/)
  assert.match(dashboardMarket, /const MARKET_REFRESH_INTERVAL = 30_000/)
  assert.match(dashboardMarket, /marketRefreshTimer = window\.setInterval/)
  assert.match(dashboardMarket, /stopMarketRefresh\(\)/)
  assert.match(dashboardMarket, /const watchStockRetryIds = new Map\(\)/)
  assert.match(dashboardMarket, /isCurrentWatchRetry\(code, snapshotRequestId, retryRequestId\)/)
})
