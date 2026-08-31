import { chromium } from 'playwright'
import fs from 'node:fs/promises'

const baseUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:52764'
const outputDir = new URL('../test-results/final-layout/', import.meta.url)
const executablePath = '/root/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell'
const routes = [
  ['market', '/'],
  ['board', '/board'],
  ['radar', '/radar'],
  ['watchlist', '/watchlist'],
  ['search', '/search?q=600519'],
  ['stock', '/stock/600519'],
  ['reports', '/reports'],
  ['report-detail', '/reports/1'],
]
const viewports = [
  ['desktop', 1440, 900],
  ['tablet', 1024, 768],
  ['mobile', 390, 844],
  ['mobile-small', 360, 800],
]
const auditStocks = [
  ['600519', '贵州茅台', 1420], ['000858', '五粮液', 118], ['601318', '中国平安', 51],
  ['600036', '招商银行', 39], ['300750', '宁德时代', 188], ['000333', '美的集团', 62],
  ['601012', '隆基绿能', 18], ['600900', '长江电力', 27], ['002594', '比亚迪', 245],
  ['600276', '恒瑞医药', 46], ['000001', '平安银行', 11], ['601888', '中国中免', 72],
]
const reportItems = Array.from({ length: 12 }, (_, index) => ({
  id: index + 1,
  report_date: `2026-08-${String(30 - index).padStart(2, '0')}`,
  status: index === 2 ? 'generating' : 'completed',
  stock_count: 12 - (index % 4),
  market_summary: index === 2 ? '' : '权重稳定，成长板块活跃度回升，关注量价确认后的持续性。',
  risk_notes: '成交缩量与高位分化仍需跟踪。',
  created_at: '2026-08-30T07:30:00Z',
  completed_at: index === 2 ? null : '2026-08-30T08:10:00Z',
}))
const reportDetail = {
  ...reportItems[0],
  user_id: 1,
  market_summary: '## 盘面结论\n\n指数窄幅整理，结构性机会集中于业绩兑现与资金回流方向。',
  risk_notes: '控制追高风险，观察成交额与核心板块持续性。',
  highlights: auditStocks.slice(0, 3).map(([stock_code, stock_name]) => ({
    stock_code, stock_name, reason: '趋势与基本面信号同步改善，纳入下一交易日观察清单。',
  })),
  stock_reports: auditStocks.slice(0, 4).map(([stock_code, stock_name, close_price], index) => ({
    id: index + 1,
    daily_report_id: 1,
    stock_code,
    stock_name,
    change_pct: index % 2 ? -0.82 : 1.26,
    close_price,
    analysis_text: `## ${stock_name}\n\n价格结构保持稳定，等待量能确认。`,
    summary: '维持观察',
    created_at: '2026-08-30T08:00:00Z',
  })),
}

async function installAuthenticatedFixtures(context) {
  await context.addInitScript(() => localStorage.setItem('stock_user_token', 'visual-audit-token'))
  await context.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname
    if (path === '/api/auth/me') return route.fulfill({ json: { id: 1, username: '视觉验收' } })
    if (path === '/api/watchlist/groups') {
      return route.fulfill({ json: [{
        id: 1, user_id: 1, name: '核心观察', sort_order: 0, created_at: '2026-08-01T00:00:00Z',
        stocks: auditStocks.map(([stock_code, stock_name, cost], index) => ({
          id: index + 1, group_id: 1, stock_code, stock_name, cost, remark: index < 3 ? '重点跟踪' : '',
          sort_order: index, created_at: '2026-08-01T00:00:00Z',
        })),
      }] })
    }
    if (path === '/api/reports') return route.fulfill({ json: { items: reportItems.slice(0, 10), total: 12, page: 1, page_size: 10 } })
    if (path === '/api/reports/1') return route.fulfill({ json: reportDetail })
    if (path === '/api/notifications/unread-count') return route.fulfill({ json: { count: 0 } })
    if (path === '/api/notifications') return route.fulfill({ json: { items: [], total: 0, page: 1, page_size: 10 } })
    const quoteMatch = path.match(/^\/api\/stock\/(\d+)$/)
    if (quoteMatch) {
      const stock = auditStocks.find(([code]) => code === quoteMatch[1])
      if (stock) {
        const [, name, price] = stock
        const index = auditStocks.indexOf(stock)
        const change_pct = index % 2 ? -0.82 : 1.26
        return route.fulfill({ json: {
          code: quoteMatch[1], name, price, change_pct,
          change_amount: Number((price * change_pct / 100).toFixed(2)),
          open: price - 1, high: price + 2, low: price - 3, volume: 1250000,
        } })
      }
    }
    return route.continue()
  })
}

await fs.mkdir(outputDir, { recursive: true })
const browser = await chromium.launch({ executablePath, headless: true })
const rows = []

for (const [viewportName, width, height] of viewports) {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 })
  await installAuthenticatedFixtures(context)
  for (const [routeName, path] of routes) {
    const page = await context.newPage()
    const errors = []
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(`console:${message.text()}`)
    })
    page.on('pageerror', (error) => errors.push(`page:${error.message}`))

    const response = await page.goto(`${baseUrl}${path}`, { waitUntil: 'commit', timeout: 10_000 })
    await page.waitForSelector('#app > *', { state: 'attached', timeout: 10_000 })
    await page.waitForTimeout(1500)
    const metrics = await page.evaluate(() => {
      const root = document.documentElement
      const body = document.body
      const overflowNodes = [...document.querySelectorAll('*')]
        .filter((element) => {
          const rect = element.getBoundingClientRect()
          return rect.width > 0 && (rect.right > root.clientWidth + 1 || rect.left < -1)
        })
        .slice(0, 6)
        .map((element) => {
          const rect = element.getBoundingClientRect()
          return {
            tag: element.tagName,
            className: String(element.className).slice(0, 100),
            left: Math.round(rect.left),
            right: Math.round(rect.right),
          }
        })
      const visibleDialogs = [...document.querySelectorAll('[role="dialog"], .el-dialog')]
        .filter((element) => {
          const style = getComputedStyle(element)
          const rect = element.getBoundingClientRect()
          return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0
        }).length
      return {
        clientWidth: root.clientWidth,
        scrollWidth: Math.max(root.scrollWidth, body.scrollWidth),
        scrollHeight: Math.max(root.scrollHeight, body.scrollHeight),
        overflowNodes,
        visibleDialogs,
      }
    })

    if (viewportName === 'desktop' || viewportName === 'mobile') {
      await page.screenshot({
        path: new URL(`${routeName}-${viewportName}.png`, outputDir).pathname,
        fullPage: true,
        animations: 'disabled',
        timeout: 10_000,
      })
    }
    const row = {
      viewport: viewportName,
      route: path,
      status: response?.status() ?? 0,
      horizontalOverflow: metrics.scrollWidth > metrics.clientWidth + 1,
      overflowNodes: metrics.overflowNodes,
      scrollHeight: metrics.scrollHeight,
      screens: Number((metrics.scrollHeight / height).toFixed(1)),
      dialogs: metrics.visibleDialogs,
      errors,
    }
    rows.push(row)
    console.log(`checked ${viewportName} ${path}`)
    await page.close()
  }
  await context.close()
}

await browser.close()
await fs.writeFile(new URL('audit.json', outputDir), JSON.stringify(rows, null, 2))
for (const row of rows) {
  const issues = []
  if (row.status !== 200) issues.push(`HTTP ${row.status}`)
  if (row.horizontalOverflow) issues.push(`overflow:${JSON.stringify(row.overflowNodes)}`)
  if (row.errors.length) issues.push(`errors:${row.errors.join('|')}`)
  console.log(
    `${row.viewport.padEnd(12)} ${row.route.padEnd(22)} screens=${String(row.screens).padEnd(4)} `
      + `dialogs=${row.dialogs} ${issues.join(' ') || 'OK'}`,
  )
}
