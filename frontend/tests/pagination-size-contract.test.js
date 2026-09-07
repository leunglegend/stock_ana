import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const paginationFiles = [
  '../src/views/Watchlist.vue',
  '../src/views/Search.vue',
  '../src/views/Reports.vue',
  '../src/views/BoardMonitor.vue',
  '../src/components/radar/BoardRanking.vue',
  '../src/components/radar/BoardStockTable.vue',
  '../src/components/board/BoardDetailPanel.vue',
]

test('所有 el-pagination 使用 size 而非已弃用的 small', async () => {
  for (const relativePath of paginationFiles) {
    const source = await readFile(new URL(relativePath, import.meta.url), 'utf8')
    const tags = source.match(/<el-pagination[\s\S]*?\/>/g) || []

    assert.ok(tags.length > 0, `${relativePath} 未找到 el-pagination`)
    for (const tag of tags) {
      assert.doesNotMatch(tag, /(?:^|\s):?small(?:\s|=|\/)/, `${relativePath} 仍在使用弃用的 small`)
      assert.match(tag, /(?:^|\s):?size\s*=/, `${relativePath} 缺少 Element Plus size 属性`)
    }
  }
})
