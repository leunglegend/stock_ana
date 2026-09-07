import assert from 'node:assert/strict'
import test from 'node:test'
import { effectScope, nextTick, ref } from 'vue'
import { toUsBoard, toUsStock } from '../src/utils/usBoardPresentation.js'
import { useUsBoardList } from '../src/composables/useUsBoardList.js'

test('美股字段适配保留有效零值、美元价格和股票代码，不伪造成交额', () => {
  const original = { name: '工业', advancers: 0, decliners: 3, constituent_count: 3, leading_symbol: 'VRT', change_pct: 0 }
  const board = toUsBoard(original)
  assert.equal(board.rise_count, 0)
  assert.equal(board.fall_count, 3)
  assert.equal(board.stock_count, 3)
  assert.equal(board.leading_stock, 'VRT')
  assert.equal(board.total_turnover, undefined)
  assert.equal(original.stock_count, undefined)
  assert.deepEqual(toUsStock({ symbol: 'BRK.B', price: 0, change_pct: 0 }), { symbol: 'BRK.B', code: 'BRK.B', price: 0, change_pct: 0 })
})

test('美股榜单按 10 条分页，筛选中英文、排序和刷新会回到第一页', async () => {
  const sectors = ref(Array.from({ length: 11 }, (_, i) => ({ name: `行业${i}`, name_en: `Sector ${i}`, change_pct: i, constituent_count: 11 - i })))
  const scope = effectScope()
  const list = scope.run(() => useUsBoardList(sectors))
  try {
    assert.equal(list.paginatedSectors.value.length, 10)
    assert.equal(list.paginatedSectors.value[0].name, '行业10')
    list.page.value = 2
    assert.equal(list.paginatedSectors.value.length, 1)
    list.keyword.value = ' sEcToR 10 '
    await nextTick()
    assert.equal(list.page.value, 1)
    assert.equal(list.filteredSectors.value.length, 1)
    list.keyword.value = '行业'
    list.sortKey.value = 'constituent_count'
    await nextTick()
    assert.equal(list.paginatedSectors.value[0].name, '行业0')
    assert.equal(sectors.value[0].name, '行业0')
    list.page.value = 2
    sectors.value = sectors.value.slice(0, 2)
    await nextTick()
    assert.equal(list.page.value, 1)
    list.keyword.value = '不存在'
    await nextTick()
    assert.equal(list.paginatedSectors.value.length, 0)
  } finally { scope.stop() }
})
