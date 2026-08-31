import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const boardTable = await readFile(
  new URL('../src/components/board/BoardTable.vue', import.meta.url),
  'utf8',
)

test('板块总成交额按接口约定的亿元单位展示', () => {
  assert.match(boardTable, /formatYi\(board\.total_turnover\)/)
  assert.match(boardTable, /import \{ formatPercent, formatYi \} from/)
  assert.doesNotMatch(boardTable, /formatAmount\(board\.total_turnover\)/)
})

test('数据源未提供换手率时显示缺失值，同时保留有效零值', () => {
  assert.match(
    boardTable,
    /board\.turnover_rate\s*==\s*null\s*\?\s*'--'\s*:\s*formatPercent\(board\.turnover_rate, 2, false\)/,
  )
})
