import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import {
  createRequestGate,
  createTimedCache,
  clearPendingRadarStock,
  filterAndSortBoards,
  normalizeOptionalMetric,
  oldestTimestamp,
  paginateRows,
  readPendingRadarStock,
  resolveValidPage,
  sortBoardStocks,
  writePendingRadarStock,
} from '../src/utils/opportunityRadar.js'

function createMockStorage() {
  const values = new Map()

  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null
    },
    setItem(key, value) {
      values.set(key, String(value))
    },
    removeItem(key) {
      values.delete(key)
    },
    keys() {
      return [...values.keys()]
    },
  }
}

test('板块按涨跌幅降序并支持名称和仅上涨过滤', () => {
  const boards = [
    { name: '银行', change_pct: 1.2 },
    { name: '半导体', change_pct: 3.8 },
    { name: '白酒', change_pct: -0.4 },
    { name: '零值', change_pct: 0 },
  ]

  assert.deepEqual(
    filterAndSortBoards(boards, { keyword: '', onlyRising: true }).map(({ name }) => name),
    ['半导体', '银行'],
  )
  assert.deepEqual(
    filterAndSortBoards(boards, { keyword: '银', onlyRising: false }).map(({ name }) => name),
    ['银行'],
  )
})

test('缺失涨幅排在真实数据之后且不修改原始板块数组', () => {
  const boards = [
    { name: '缺失' },
    { name: '平盘', change_pct: 0 },
    { name: '上涨', change_pct: 1 },
  ]
  const snapshot = structuredClone(boards)

  assert.deepEqual(filterAndSortBoards(boards).map(({ name }) => name), ['上涨', '平盘', '缺失'])
  assert.deepEqual(boards, snapshot)
})

test('缺失指标与真实零值保持可区分', () => {
  assert.equal(normalizeOptionalMetric(undefined), null)
  assert.equal(normalizeOptionalMetric(Number.NaN), null)
  assert.equal(normalizeOptionalMetric('0'), null)
  assert.equal(normalizeOptionalMetric(0), 0)
})

test('成分股按涨跌幅降序且分页不修改输入数组', () => {
  const rows = Array.from({ length: 25 }, (_, index) => ({
    code: String(index),
    change_pct: index === 24 ? undefined : index,
  }))
  const sorted = sortBoardStocks(rows)

  assert.equal(sorted[0].change_pct, 23)
  assert.equal(sorted.at(-1).code, '24')
  assert.deepEqual(paginateRows(sorted, 2, 20), sorted.slice(20))
  assert.equal(rows[0].code, '0')
})

test('定时缓存命中后会在 60 秒过期', () => {
  let now = 1000
  const cache = createTimedCache(60_000, () => now)

  cache.set('industry', ['cached'])
  assert.deepEqual(cache.get('industry'), ['cached'])
  now = 61_001
  assert.equal(cache.get('industry'), undefined)
})

test('定时缓存支持显式删除与清空', () => {
  const cache = createTimedCache(60_000, () => 1000)
  cache.set('industry', [1])
  cache.set('concept', [2])
  cache.delete('industry')
  assert.equal(cache.get('industry'), undefined)
  cache.clear()
  assert.equal(cache.get('concept'), undefined)
})

test('请求 gate 只接受同一频道最后一次请求', () => {
  const gate = createRequestGate()
  const first = gate.next('stocks')
  const second = gate.next('stocks')

  assert.equal(gate.isCurrent('stocks', first), false)
  assert.equal(gate.isCurrent('stocks', second), true)
  gate.invalidate('stocks')
  assert.equal(gate.isCurrent('stocks', second), false)
})

test('数据总数缩水时将页码回收到最后一个有效页', () => {
  assert.equal(resolveValidPage(2, 40, 20), 2)
  assert.equal(resolveValidPage(2, 20, 20), 1)
  assert.equal(resolveValidPage(3, 0, 20), 1)
})

test('共同更新时间取可见数据中较旧的成功时间', () => {
  assert.equal(oldestTimestamp(1000, 1200), 1000)
  assert.equal(oldestTimestamp(null, 1200), 1200)
  assert.equal(oldestTimestamp(null, undefined), null)
})

test('挂起雷达股票可安全写入读取并清理，且只保留 code 和 name', () => {
  const storage = createMockStorage()

  writePendingRadarStock(storage, { code: '600000', name: '浦发银行', extra: 'ignored' })

  assert.deepEqual(readPendingRadarStock(storage), { code: '600000', name: '浦发银行' })
  clearPendingRadarStock(storage)
  assert.equal(readPendingRadarStock(storage), null)
})

test('挂起雷达股票对无效 code、坏 JSON 和默认 storage 安全降级', () => {
  const storage = createMockStorage()

  writePendingRadarStock(storage, { code: '', name: '无效' })
  assert.equal(readPendingRadarStock(storage), null)
  writePendingRadarStock(storage, { code: '000001', name: '平安银行' })
  storage.setItem(storage.keys()[0], '{bad json')
  assert.equal(readPendingRadarStock(storage), null)
  assert.equal(readPendingRadarStock(), null)
})

test('挂起雷达股票在存储访问异常时不抛错', () => {
  const storage = {
    getItem() { throw new Error('read failed') },
    setItem() { throw new Error('write failed') },
    removeItem() { throw new Error('remove failed') },
  }

  assert.doesNotThrow(() => readPendingRadarStock(storage))
  assert.doesNotThrow(() => writePendingRadarStock(storage, { code: '600519', name: '贵州茅台' }))
  assert.doesNotThrow(() => clearPendingRadarStock(storage))
})

test('雷达组合式函数集中持有三个现有板块 API 与请求保护', async () => {
  const source = await readFile(
    new URL('../src/composables/useOpportunityRadar.js', import.meta.url),
    'utf8',
  )

  assert.match(source, /getBoardIndustry/)
  assert.match(source, /getBoardConcept/)
  assert.match(source, /getBoardStocks/)
  assert.match(source, /createRequestGate/)
  assert.match(source, /createTimedCache/)
  assert.match(source, /Promise\.allSettled/)
})

test('雷达分页总数来自实际加载的成分股数据', async () => {
  const source = await readFile(
    new URL('../src/composables/useOpportunityRadar.js', import.meta.url),
    'utf8',
  )

  assert.match(source, /const stockTotal = computed\(\(\) => stockState\.data\.length\)/)
  assert.match(source, /\bstockTotal,/)
})

test('自动加载成分股会消费接口失败并交给错误状态展示', async () => {
  const source = await readFile(
    new URL('../src/composables/useOpportunityRadar.js', import.meta.url),
    'utf8',
  )

  assert.match(source, /void loadStocks\([^\n]+\)\.catch\(\(\) => \{\}\)/)
})

test('成分股总数变化时组合式函数会回收无效页码', async () => {
  const source = await readFile(
    new URL('../src/composables/useOpportunityRadar.js', import.meta.url),
    'utf8',
  )

  assert.match(source, /watch\(\[stockTotal, stockPageSize\],[\s\S]*resolveValidPage/)
})

test('板块总数变化时组合式函数会回收无效页码', async () => {
  const source = await readFile(
    new URL('../src/composables/useOpportunityRadar.js', import.meta.url),
    'utf8',
  )

  assert.match(source, /const BOARD_PAGE_SIZE = 10/)
  assert.match(source, /watch\(filteredBoards,[\s\S]*boardPage\.value = resolveValidPage\([\s\S]*BOARD_PAGE_SIZE\)/)
})
