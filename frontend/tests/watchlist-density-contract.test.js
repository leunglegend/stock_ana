import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const watchlistSource = await readFile(new URL('../src/views/Watchlist.vue', import.meta.url), 'utf8')
const groupTabsSource = await readFile(new URL('../src/components/watchlist/GroupTabs.vue', import.meta.url), 'utf8')
const filtersSource = await readFile(new URL('../src/components/watchlist/WatchlistFilters.vue', import.meta.url), 'utf8')
const tableSource = await readFile(new URL('../src/components/watchlist/WatchlistTable.vue', import.meta.url), 'utf8')
const mobileListSource = await readFile(new URL('../src/components/watchlist/WatchlistMobileList.vue', import.meta.url), 'utf8')
const signalSource = await readFile(new URL('../src/components/watchlist/WatchlistSignalCenter.vue', import.meta.url), 'utf8')
const searchSource = await readFile(new URL('../src/components/StockSearch.vue', import.meta.url), 'utf8')

test('自选主表先于信号摘要，工具区不使用英文 eyebrow', () => {
  assert.ok(watchlistSource.indexOf('<WatchlistTable') < watchlistSource.indexOf('<WatchlistSignalCenter'))
  assert.doesNotMatch(watchlistSource, /watchlist-page__eyebrow/)
  assert.doesNotMatch(groupTabsSource, /group-tabs__eyebrow/)
})

test('信号中心仅展开前三条结果，使用紧凑统计与待处理队列', () => {
  assert.match(signalSource, /orderedResults\.value\.slice\(0, 3\)/)
  assert.match(signalSource, /signal-center__stats/)
  assert.match(signalSource, /signal-center__todo/)
  assert.match(signalSource, /min-height:\s*66px/)
  assert.match(signalSource, /@click="\$emit\('scan'\)"/)
})

test('自选工具区和结果表使用数据终端密度', () => {
  assert.match(filtersSource, /class="watchlist-filters__toolbar"/)
  assert.match(tableSource, /min-height:\s*var\(--data-row-height\)/)
  assert.match(tableSource, /<el-dropdown/)
  assert.match(tableSource, /label="更多"/)
})

test('移动端一行一只且低频操作收进更多菜单', () => {
  assert.match(mobileListSource, /min-height:\s*68px/)
  assert.match(mobileListSource, /max-height:\s*76px/)
  assert.match(mobileListSource, /<el-dropdown/)
  assert.doesNotMatch(mobileListSource, /watchlist-mobile__actions/)
})

test('自选与添加搜索组件不再包含组件级 raw color 或阴影卡片', () => {
  ;[filtersSource, groupTabsSource, tableSource, mobileListSource, signalSource, searchSource].forEach((source) => {
    const styles = source.match(/<style scoped>([\s\S]*?)<\/style>/)?.[1] || ''
    assert.doesNotMatch(styles, /#[0-9a-f]{3,8}/i)
    assert.doesNotMatch(styles, /box-shadow:\s*(?!none)/)
  })
})
