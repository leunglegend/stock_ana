import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const searchSource = await readFile(new URL('../src/views/Search.vue', import.meta.url), 'utf8')
const watchlistSource = await readFile(new URL('../src/views/Watchlist.vue', import.meta.url), 'utf8')

test('新搜索会先清空旧结果并复位分页', () => {
  const submitSearch = searchSource.match(/async function submitSearch\(\) \{([\s\S]*?)\n\}/)?.[1] || ''

  assert.match(submitSearch, /const requestId = \+\+searchRequestId/)
  assert.match(submitSearch, /currentPage\.value = 1/)
  assert.match(submitSearch, /results\.value = \[\]/)
  assert.ok(submitSearch.indexOf('results.value = []') < submitSearch.indexOf("viewState.value = 'loading'"))
})

test('清空路由搜索词会让在途请求失效并回到第一页', () => {
  const routeWatcher = searchSource.match(/watch\(\(\) => route\.query\.q, \(query\) => \{([\s\S]*?)\n\}\)/)?.[1] || ''

  assert.match(routeWatcher, /searchRequestId \+= 1/)
  assert.match(routeWatcher, /results\.value = \[\]/)
  assert.match(routeWatcher, /currentPage\.value = 1/)
})

test('搜索和自选分页在移动端仅保留前后翻页与页状态文本', () => {
  ;[searchSource, watchlistSource].forEach((source) => {
    assert.match(source, /const paginationLayout = computed\(\(\) => isMobile\.value \? 'prev, next' : 'total, prev, pager, next'\)/)
    assert.match(source, /:layout="paginationLayout"/)
    assert.match(source, /v-if="isMobile" class="[^"]*__page-status" aria-live="polite">第 \{\{ currentPage \}\} \/ \{\{ pageCount \}\} 页<\/span>/)
    assert.doesNotMatch(source, /paginationPagerCount/)
  })
})
