import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const stockDetail = await readFile(new URL('../src/views/StockDetail.vue', import.meta.url), 'utf8')
const search = await readFile(new URL('../src/views/Search.vue', import.meta.url), 'utf8')
const reportDetail = await readFile(new URL('../src/views/ReportDetail.vue', import.meta.url), 'utf8')
const kline = await readFile(new URL('../src/components/KLineChart.vue', import.meta.url), 'utf8')
const financial = await readFile(new URL('../src/components/FinancialCard.vue', import.meta.url), 'utf8')
const advice = await readFile(new URL('../src/components/AiAdvice.vue', import.meta.url), 'utf8')

test('个股页仅保留一份行情事实且 K 线为主研究区', () => {
  assert.equal((stockDetail.match(/<QuoteFacts/g) || []).length, 1)
  assert.ok(stockDetail.indexOf('stock-detail-page__chart') < stockDetail.indexOf('stock-detail-page__research'))
  assert.doesNotMatch(stockDetail, /label="行情"|label="K 线"/)
})

test('搜索将计数和排序控制紧邻结果列表', () => {
  assert.doesNotMatch(search, /Command Search|search-page__eyebrow/)
  assert.match(search, /search-page__result-toolbar/)
  assert.match(search, /resultSort/)
  assert.match(search, /\{\{ results\.length \}\} 条结果/)
})

test('报告详情先显示结论、风险与关联股票，正文宽度受控', () => {
  const conclusion = reportDetail.indexOf('今日结论')
  const risk = reportDetail.indexOf('风险提示')
  const highlights = reportDetail.indexOf('关联股票')
  const analysis = reportDetail.indexOf('个股分析')

  assert.ok(conclusion < risk && risk < highlights && highlights < analysis)
  assert.match(reportDetail, /function openStock\(code\)/)
  assert.match(reportDetail, /max-width: 68ch/)
})

test('研究组件不再使用普通卡片或英文 eyebrow', () => {
  ;[kline, financial, advice].forEach((source) => {
    assert.doesNotMatch(source, /el-card|card-shadow|eyebrow/)
  })
})
