import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const root = new URL('../src/', import.meta.url)
const api = await readFile(new URL('api/stock.js', root), 'utf8')
const view = await readFile(new URL('views/StockDetail.vue', root), 'utf8')
const component = await readFile(new URL('components/stock/DecisionReport.vue', root), 'utf8')
const markdown = await readFile(new URL('utils/markdown.js', root), 'utf8')

test('决策报告 API 使用现有 HTTP 封装并保留独立 endpoint', () => {
  assert.match(api, /getStockDecisionReport\(code\)/)
  assert.match(api, /http\.get\(`\/stock\/\$\{code\}\/decision-report`\)/)
})

test('个股页提供独立决策报告标签并切到时按需加载', () => {
  assert.match(view, /<el-tab-pane label="决策报告" name="decision">/)
  assert.match(view, /<DecisionReport[\s\S]*:report="decisionReport"/)
  // 决策报告生成走 AI（慢且耗 token），只在切到该标签时懒加载一次
  assert.match(view, /@tab-change="handleTabChange"/)
  assert.match(view, /tabName === 'decision' && !decisionLoaded\) loadDecisionReport\(pageGeneration\)/)
  assert.match(view, /let decisionRequestId = 0/)
  assert.match(view, /decisionReport\.value = null/)
  assert.match(view, /decisionRequestId, targetCode/)
})

test('报告组件覆盖状态、重试和结构化报告区块', () => {
  ;['idle', 'loading', 'error', 'empty'].forEach((state) => assert.match(component, new RegExp(`state === '${state}'|state=\"${state}\"`)))
  assert.match(component, /@retry/)
  ;['综合结论', '趋势与技术信号', '关键价位', '风险与催化', '数据限制', '操作检查清单'].forEach((label) => assert.match(component, new RegExp(label)))
  assert.match(component, /renderSafeMarkdown/)
  assert.match(component, /仅供参考，不构成投资建议/)
})

test('报告使用既有设计变量和移动端断点，不引入独立卡片体系', () => {
  assert.match(component, /--spacing-/)
  assert.match(component, /--surface-primary|--border-subtle/)
  assert.match(component, /--text-primary|--text-tertiary/)
  assert.doesNotMatch(component, /el-card|card-shadow/)
  assert.match(view, /@media \(max-width: 1023px\)/)
  assert.match(view, /@media \(max-width: 767px\)/)
})

test('报告正文继续走安全 Markdown 渲染器', () => {
  assert.match(component, /v-html="renderedMarkdown"/)
  assert.match(component, /renderSafeMarkdown\(props\.report\?\.analysis_markdown \|\| ''\)/)
  assert.match(markdown, /ALLOWED_TAGS/)
  assert.match(markdown, /SAFE_PROTOCOLS/)
})
