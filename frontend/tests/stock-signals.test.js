import assert from 'node:assert/strict'
import test from 'node:test'

import {
  analyzeStockSignals,
  summarizeSignalResults,
} from '../src/utils/stockSignals.js'

function makeRows(closes) {
  return closes.map((close, index) => ({
    date: `2026-08-${String(index + 1).padStart(2, '0')}`,
    open: close - 1,
    close,
    high: close + 1,
    low: close - 2,
    volume: 10000 + index * 100,
    ma5: close - 2,
    ma20: close - 5,
    dif: 0.1,
    dea: 0.05,
    macd: 0.1,
    rsi6: 55,
  }))
}

test('上升趋势、MACD 金叉、突破和成本收益形成偏强结果', () => {
  const rows = makeRows(Array.from({ length: 21 }, (_, index) => 100 + index))
  rows[19].dif = 0.1
  rows[19].dea = 0.2
  rows[20] = {
    ...rows[20],
    close: 125,
    high: 126,
    ma5: 122,
    ma20: 112,
    dif: 0.35,
    dea: 0.2,
    macd: 0.3,
    rsi6: 64,
  }

  const result = analyzeStockSignals({ kline: rows }, { costReturn: 0.18 })

  assert.equal(result.status, 'strong')
  assert.deepEqual(result.signals.map(({ code }) => code), [
    'trend-above-ma20',
    'macd-golden-cross',
    'breakout-20d',
    'cost-gain',
  ])
})

test('弱趋势、MACD 死叉、过热、明显回撤和成本亏损形成关注结果', () => {
  const rows = makeRows(Array.from({ length: 21 }, (_, index) => 100 + index * 0.2))
  rows[19].dif = 0.4
  rows[19].dea = 0.2
  rows[20] = {
    ...rows[20],
    close: 88,
    high: 90,
    ma5: 91,
    ma20: 98,
    dif: 0.1,
    dea: 0.3,
    macd: -0.4,
    rsi6: 78,
  }

  const result = analyzeStockSignals({ kline: rows }, { costReturn: -0.12 })

  assert.equal(result.status, 'attention')
  assert.deepEqual(result.signals.map(({ code }) => code), [
    'trend-below-ma20',
    'macd-death-cross',
    'rsi-overheated',
    'drawdown-20d',
    'cost-loss',
  ])
})

test('RSI 超卖被描述为位置状态而不是买入建议', () => {
  const rows = makeRows([100, 98, 96])
  rows[2].rsi6 = 22

  const result = analyzeStockSignals({ kline: rows })
  const signal = result.signals.find(({ code }) => code === 'rsi-oversold')

  assert.equal(signal.kind, 'info')
  assert.match(signal.label, /超卖区间/)
  assert.doesNotMatch(signal.label, /买入|抄底/)
})

test('空数据和非有限指标返回中性的数据不足结果', () => {
  const result = analyzeStockSignals({ kline: [{ close: Number.NaN }] })

  assert.equal(result.status, 'neutral')
  assert.deepEqual(result.signals, [])
  assert.equal(result.note, '有效 K 线数据不足')
})

test('汇总结果分别统计偏强、中性、关注和失败', () => {
  const summary = summarizeSignalResults([
    { status: 'success', analysis: { status: 'strong' } },
    { status: 'success', analysis: { status: 'strong' } },
    { status: 'success', analysis: { status: 'neutral' } },
    { status: 'success', analysis: { status: 'attention' } },
    { status: 'error' },
  ])

  assert.deepEqual(summary, { total: 5, strong: 2, neutral: 1, attention: 1, error: 1 })
})

test('阈值边界会稳定命中且不会修改原始 K 线数组', () => {
  const rows = makeRows(Array.from({ length: 21 }, (_, index) => 100 + index * 0.1))
  rows[20] = { ...rows[20], close: 90, ma5: 92, ma20: 95, rsi6: 75 }
  const snapshot = structuredClone(rows)

  const result = analyzeStockSignals({ kline: rows }, { costReturn: -0.1 })

  assert.equal(result.status, 'attention')
  assert.ok(result.signals.some(({ code }) => code === 'rsi-overheated'))
  assert.ok(result.signals.some(({ code }) => code === 'cost-loss'))
  assert.deepEqual(rows, snapshot)
})

test('位置判断只使用最近 20 个前序交易日并忽略缺失最高价', () => {
  const rows = makeRows(Array.from({ length: 25 }, () => 100))
  rows[0].high = 200
  rows.slice(1, 24).forEach((row) => { row.high = Number.NaN })
  rows[23].high = 105
  rows[24] = { ...rows[24], close: 106, high: 107 }

  const result = analyzeStockSignals({ kline: rows })

  assert.ok(result.signals.some(({ code }) => code === 'breakout-20d'))
})

test('扫描中的结果计入总数但不误计为已完成分类', () => {
  const summary = summarizeSignalResults([
    { status: 'loading' },
    { status: 'success', analysis: { status: 'neutral' } },
  ])

  assert.deepEqual(summary, { total: 2, strong: 0, neutral: 1, attention: 0, error: 0 })
})
