import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const view = await readFile(new URL('../src/views/Watchlist.vue', import.meta.url), 'utf8')
const table = await readFile(new URL('../src/components/watchlist/WatchlistTable.vue', import.meta.url), 'utf8')
const mobile = await readFile(new URL('../src/components/watchlist/WatchlistMobileList.vue', import.meta.url), 'utf8')
const inspector = await readFile(new URL('../src/components/watchlist/WatchlistSignalCenter.vue', import.meta.url), 'utf8')

test('自选页将标题操作、同一工具栏和 320px 待处理检查器组织为连续工作面', () => {
  assert.match(view, /<header[\s\S]*Refresh[\s\S]*添加股票[\s\S]*<\/header>/)
  assert.match(view, /class="watchlist-page__toolbar"/)
  assert.match(view, /class="watchlist-page__workspace"/)
  assert.match(view, /class="watchlist-page__inspector"/)
  assert.match(view, /grid-template-columns:\s*minmax\(0,\s*1fr\)\s+320px/)
  assert.ok(view.indexOf('<WatchlistTable') < view.indexOf('<WatchlistSignalCenter'))
})

test('待处理检查器提供四项扫描统计与前三条研究队列', () => {
  assert.match(inspector, /class="signal-center__stats"/)
  assert.match(inspector, /orderedResults\.value\.slice\(0,\s*3\)/)
  assert.match(inspector, /class="signal-center__todo"/)
  assert.match(inspector, /另有 \{\{ hiddenCount \}\} 只已完成扫描/)
})

test('桌面表格、平板核心列和移动行保留 v1 的扫描密度', () => {
  assert.match(table, /height:\s*var\(--data-row-height\)/)
  assert.match(table, /@media\s*\(min-width:\s*768px\)\s*and\s*\(max-width:\s*1023px\)/)
  assert.match(table, /watchlist-table__desktop-detail/)
  assert.match(mobile, /min-height:\s*68px/)
  assert.match(mobile, /max-height:\s*76px/)
  assert.match(mobile, /<el-dropdown/)
})
