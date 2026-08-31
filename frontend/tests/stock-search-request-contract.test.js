import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = await readFile(new URL('../src/components/StockSearch.vue', import.meta.url), 'utf8')

test('远程搜索只接受当前查询的最后一次响应', () => {
  assert.match(source, /let searchRequestId = 0/)
  assert.match(source, /const requestId = \+\+searchRequestId/)
  assert.match(source, /function isCurrentSearch\(requestId, query\)/)
  assert.match(source, /requestId === searchRequestId && query === keyword\.value/)
  assert.match(source, /if \(!isCurrentSearch\(requestId, query\)\) return/)
})

test('卸载时清理防抖计时器并使在途搜索失效', () => {
  assert.match(source, /import \{[^}]*onBeforeUnmount[^}]*\} from 'vue'/)
  assert.match(source, /onBeforeUnmount\(\(\) => \{[\s\S]*clearTimeout\(searchTimer\)[\s\S]*searchRequestId \+= 1/)
})
