import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const boardMonitor = await readFile(new URL('../src/views/BoardMonitor.vue', import.meta.url), 'utf8')
const boardDetail = await readFile(new URL('../src/components/board/BoardDetailPanel.vue', import.meta.url), 'utf8')
const radar = await readFile(new URL('../src/views/OpportunityRadar.vue', import.meta.url), 'utf8')
const snapshot = await readFile(new URL('../src/components/radar/BoardSnapshot.vue', import.meta.url), 'utf8')
const stockTable = await readFile(new URL('../src/components/radar/BoardStockTable.vue', import.meta.url), 'utf8')
const ranking = await readFile(new URL('../src/components/radar/BoardRanking.vue', import.meta.url), 'utf8')
const radarComposable = await readFile(new URL('../src/composables/useOpportunityRadar.js', import.meta.url), 'utf8')

test('板块发现以 58:42 的连续主从工作面承载排行与检查器', () => {
  assert.match(boardMonitor, /board-page__workspace/)
  assert.match(boardMonitor, /grid-template-columns: minmax\(0, 58fr\) minmax\(0, 42fr\)/)
  assert.match(boardMonitor, /board-page__toolbar[\s\S]*<el-tabs[\s\S]*board-page__filters[\s\S]*board-page__pager/)
  assert.match(boardDetail, /board-detail__facts/)
  assert.match(boardDetail, /总成交额|成交额/)
  assert.match(boardDetail, /覆盖个股|成分股/)
})

test('机会雷达使用四格结果摘要和 30:70 候选工作面', () => {
  assert.match(radar, /radar-page__summary-strip/)
  assert.match(radar, /强势板块/)
  assert.match(radar, /扩散率/)
  assert.match(radar, /强势领涨股/)
  assert.match(radar, /当前候选/)
  assert.match(radar, /grid-template-columns: minmax\(0, 30fr\) minmax\(0, 70fr\)/)
  assert.match(snapshot, /board-snapshot--context/)
})

test('雷达候选表把信号和加入自选保留在连续表格中', () => {
  assert.match(stockTable, /信号/)
  assert.match(stockTable, /加入自选/)
  assert.match(stockTable, /board-stock-table__desktop/)
  assert.doesNotMatch(stockTable, /board-stock-table__card\s*\{[\s\S]*border-radius:/)
})

test('移动雷达候选行保留换手率、信号和加入自选', () => {
  const mobileList = stockTable.match(/<div v-else class="board-stock-table__mobile"[\s\S]*?<\/div>\n    <\/div>/)?.[0] || ''
  assert.match(mobileList, /board-stock-table__mobile-row/)
  assert.match(mobileList, /最新价/)
  assert.match(mobileList, /信号/)
  assert.match(mobileList, />加入<\/el-button>/)
  assert.match(mobileList, /\$emit\('open-stock', row\.code\)/)
  assert.doesNotMatch(mobileList, /换手率|查看详情|card-metrics|card-actions/)
  assert.match(stockTable, /min-height:\s*72px/)
})

test('平板及手机优先展示雷达候选表而非板块索引', () => {
  assert.match(
    radar,
    /@media \(max-width: 1023px\) \{[\s\S]*\.radar-page__detail\s*\{[\s\S]*(?:order:\s*-1|grid-row:\s*1)/,
  )
})

test('中等桌面宽度下雷达工作区收敛为单列以避免表格溢出', () => {
  assert.match(
    radar,
    /@media \(max-width:\s*1279px\)\s*\{[\s\S]*\.radar-page__workspace\s*\{[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)/,
  )
  assert.match(
    radar,
    /@media \(max-width:\s*1279px\)\s*\{[\s\S]*\.radar-page__detail\s*\{[\s\S]*(?:order:\s*-1|grid-row:\s*1)/,
  )
})

test('雷达紧凑视图分页仅显示前后页和页码状态', () => {
  for (const source of [ranking, stockTable]) {
    assert.match(source, /:layout="(?:compact|mobile) \? 'prev, next' : 'prev, pager, next'"/)
    assert.match(source, /第 \{\{ (?:page|resolvedPage) \}\} \/ \{\{ (?:pageCount|resolvedPageCount) \}\} 页/)
  }
})

test('雷达候选在桌面每页二十条，紧凑端每页十条', () => {
  assert.match(radar, /:page-size="stockPageSize"/)
  assert.match(radarComposable, /const MOBILE_STOCK_PAGE_SIZE = 10/)
  assert.match(radarComposable, /const stockPageSize = computed\(\(\) => isDesktop\.value \? STOCK_PAGE_SIZE : MOBILE_STOCK_PAGE_SIZE\)/)
  assert.match(radarComposable, /paginateRows\(stockState\.data, stockPage\.value, stockPageSize\.value\)/)
})

test('机会雷达不保留生产调试日志', () => {
  assert.doesNotMatch(radar, /console\.(?:log|info|debug)|radar-debug|Error\(\)\.stack/)
})

test('雷达缓存命中会使旧成分股请求失效', () => {
  const loadStocks = radarComposable.match(/async function loadStocks\([\s\S]*?\n  \}/)?.[0] || ''
  const cachedBranch = loadStocks.match(/if \(cached\) \{[\s\S]*?\n    \}/)?.[0] || ''
  assert.match(cachedBranch, /requestGate\.invalidate\('stocks'\)/)
  assert.match(cachedBranch, /stockState\.pending = null/)
})

test('板块列表重试后重新按当前深链恢复详情', () => {
  const retry = boardMonitor.match(/async function retryActiveSection\(\) \{[\s\S]*?\n\}/)?.[0] || ''
  assert.match(retry, /await syncBoardFromRoute\(\)/)
})

test('雷达待加入股票明确使用默认 session storage', () => {
  assert.match(radar, /writePendingRadarStock\(undefined, nextStock\)/)
})

test('板块与雷达视图保持在 300 行以内', () => {
  assert.ok(boardMonitor.split('\n').length <= 300)
  assert.ok(radar.split('\n').length <= 300)
})
