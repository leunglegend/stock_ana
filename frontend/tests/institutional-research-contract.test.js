import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [search, searchResults, reports, reportTable, reportDetail, outline, markdown] = await Promise.all([
  readFile(new URL('../src/views/Search.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/stock/SearchResults.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/views/Reports.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/reports/ReportTable.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/views/ReportDetail.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/reports/ReportOutline.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/utils/markdown.js', import.meta.url), 'utf8'),
])

test('搜索页将标题、最近搜索、输入带与结果控制组织为连续研究流', () => {
  assert.match(search, /search-page__recent-line/)
  assert.match(search, /search-page__input-strip/)
  assert.match(search, /search-page__result-toolbar/)
  assert.match(search, /:items="paginatedResults"/)
})

test('搜索结果在桌面端使用连续表格，在移动端保留紧凑且可操作的结果行', () => {
  assert.match(searchResults, /<table[^>]*class="search-results__table"/)
  assert.match(searchResults, /<th[^>]*>股票<\/th>/)
  assert.match(searchResults, /search-results__row[^\n]*min-height:\s*44px/)
  assert.match(searchResults, /@media\s*\(max-width:\s*767px\)/)
})

test('搜索请求失败显示可重试错误状态，而非空结果', () => {
  assert.match(search, /viewState\.value = 'error'/)
  assert.match(search, /@retry-search="submitSearch"/)
  assert.match(searchResults, /v-else-if="state === 'error'"/)
  assert.match(searchResults, /state="error"/)
  assert.match(searchResults, /@retry="\$emit\('retry-search'\)"/)
  assert.match(searchResults, /'retry-search'/)
})

test('报告列表按日期、状态、重点股票、结论风险和完成时间呈现连续列', () => {
  assert.match(reports, /reports-page__toolbar/)
  assert.match(reportTable, /<thead>/)
  ;['日期', '状态', '重点股票', '今日结论 \/ 风险', '完成时间'].forEach((label) => {
    assert.match(reportTable, new RegExp(label))
  })
  assert.match(reportTable, /report-table__risk/)
  assert.match(reportTable, /详情查看风险/)
  assert.match(reportTable, /report-table__row \{ height:\s*44px/)
  assert.match(reportTable, /report-table td \{[^}]*height:\s*44px/)
  assert.match(reportTable, /text-overflow:\s*ellipsis/)
  assert.equal((reports.match(/<el-select/g) || []).length, 2)
})

test('报告详情使用 180px 目录和受控阅读列，并在正文前展示结论、风险和关联股票', () => {
  assert.match(reportDetail, /report-detail-page__summary/)
  assert.match(reportDetail, /max-width:\s*(?:68ch|760px)/)
  assert.ok(reportDetail.indexOf('今日结论') < reportDetail.indexOf('风险提示'))
  assert.ok(reportDetail.indexOf('风险提示') < reportDetail.indexOf('关联股票'))
  assert.match(outline, /width:\s*180px/)
  ;['今日结论', '风险提示', '关联股票', '个股分析'].forEach((label) => {
    assert.match(reportDetail, new RegExp(`label: '${label}'`))
  })
})

test('报告 Markdown 保持白名单和安全链接处理', () => {
  assert.match(markdown, /ALLOWED_TAGS/)
  assert.match(markdown, /SAFE_PROTOCOLS/)
  assert.match(markdown, /noopener noreferrer/)
})

test('报告详情视图保持在单文件行数上限内', () => {
  const lines = reportDetail.split('\n').length - 1
  assert.ok(lines <= 300, `ReportDetail.vue 当前 ${lines} 行，超过 300 行上限`)
})
