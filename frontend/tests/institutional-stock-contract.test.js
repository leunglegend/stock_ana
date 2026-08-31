import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const stockDetail = await readFile(new URL('../src/views/StockDetail.vue', import.meta.url), 'utf8')
const stockHeader = await readFile(new URL('../src/components/stock/StockHeader.vue', import.meta.url), 'utf8')
const quoteFacts = await readFile(new URL('../src/components/stock/QuoteFacts.vue', import.meta.url), 'utf8')
const kline = await readFile(new URL('../src/components/KLineChart.vue', import.meta.url), 'utf8')
const financial = await readFile(new URL('../src/components/FinancialCard.vue', import.meta.url), 'utf8')
const advice = await readFile(new URL('../src/components/AiAdvice.vue', import.meta.url), 'utf8')

test('个股页以身份价格带和 72:28 主从研究工作面组织内容', () => {
  assert.match(stockDetail, /<StockHeader class="[^"]*stock-detail-page__identity-band/)
  assert.match(stockDetail, /<section class="stock-detail-page__workspace"/)
  assert.match(stockDetail, /grid-template-columns:\s*minmax\(0,\s*72fr\)\s+minmax\(280px,\s*28fr\)/)
  assert.ok(stockDetail.indexOf('stock-detail-page__chart') < stockDetail.indexOf('stock-detail-page__research'))
  assert.match(stockDetail, /@media \(max-width: 1023px\)[\s\S]*stock-detail-page__workspace[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)/)
})

test('检查器只保留一份行情事实，财务和 AI 仅替换其研究内容', () => {
  assert.equal((stockDetail.match(/<QuoteFacts/g) || []).length, 1)
  assert.match(stockDetail, /<aside class="stock-detail-page__research">[\s\S]*<QuoteFacts[\s\S]*<el-tabs/)
  assert.match(stockDetail, /const activeTab = ref\('financial'\)/)
  assert.doesNotMatch(stockDetail, /label="行情"|label="K 线"/)
})

test('身份带、行情事实和图表在窄屏保持可扫描的单列密度', () => {
  assert.match(stockHeader, /stock-header--identity/)
  assert.match(stockHeader, /@media \(max-width: 767px\)[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+auto/)
  assert.match(quoteFacts, /grid-template-columns:\s*repeat\(3, minmax\(0, 1fr\)\)/)
  assert.match(quoteFacts, /@media \(max-width: 767px\)[\s\S]*repeat\(2, minmax\(0, 1fr\)\)/)
  assert.match(kline, /@media \(max-width:767px\)[\s\S]*kline-card__chart\{height:420px\}/)
})

test('右侧研究组件保持连续检查器，而非普通浮层卡片', () => {
  ;[financial, advice].forEach((source) => assert.doesNotMatch(source, /el-card|card-shadow/))
  assert.match(financial, /financial-card__grid/)
  assert.match(advice, /ai-advice-card__body/)
})

test('AI 摘要以分隔行而非嵌套圆角卡片呈现，行情事实标题保持紧凑', () => {
  ;['placeholder', 'notice', 'action', 'score-panel'].forEach((part) => {
    assert.doesNotMatch(advice, new RegExp(`\\.ai-advice-card__${part}[^\\{]*\\{[^}]*border-radius`))
  })
  assert.doesNotMatch(advice, /ai-advice-card__score-panel\{[^}]*padding:var\(--spacing-5\)/)
  assert.match(advice, /ai-advice-card__score-panel\{[^}]*border-top:1px solid var\(--border-subtle\)/)
  assert.match(quoteFacts, /quote-facts__title[\s\S]*font-size: var\(--font-size-sm\)/)
})
