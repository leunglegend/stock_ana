import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

async function read(relativePath) {
  return readFile(new URL(relativePath, import.meta.url), 'utf8')
}

const [viewSource, tableSource, queueSource, headerSource] = await Promise.all([
  read('../src/views/Monitor.vue'),
  read('../src/components/monitor/MonitorTable.vue'),
  read('../src/components/monitor/MonitorActionQueue.vue'),
  read('../src/components/monitor/MonitorHeader.vue'),
])

test('监控页面组合市场、队列、矩阵和检查器', () => {
  assert.match(viewSource, /class="[^"]*monitor-page[^\"]*workbench-page/)
  assert.match(headerSource, /data-page-title[^>]*>盘中监控</)
  assert.match(viewSource, /getMonitorOverview/)
  assert.match(viewSource, /setInterval/)
  assert.match(viewSource, /MonitorActionQueue/)
  assert.match(viewSource, /MonitorTable/)
  assert.match(viewSource, /MonitorInspector/)
})

test('监控矩阵和行动队列提供可访问交互', () => {
  assert.match(tableSource, /aria-label="自选股监控矩阵"/)
  assert.match(tableSource, /aria-selected/)
  assert.match(queueSource, /emit\(['"]open-stock['"]/)
  assert.match(headerSource, /aria-label="刷新盘中监控"/)
  assert.match(headerSource, /refreshError/)
})

test('监控页面声明过期、错误和个股跳转处理', async () => {
  assert.match(viewSource, /isStale/)
  assert.match(viewSource, /StatusState/)
  assert.match(viewSource, /router\.push\([\s\S]*path: `\/stock\//)
  assert.match(viewSource, /financialState/)
  assert.match(viewSource, /isTradingSession/)
  assert.match(viewSource, /管理自选股/)
  assert.match(viewSource, /startAnalyze/)
  assert.match(viewSource, /@retry="retryItem"/)
  assert.match(headerSource, /refreshError/)
  assert.match(tableSource, /相对上证/)
  assert.match(tableSource, /formatFetchTime/)
  assert.match(viewSource, /refresh-error/)
  assert.match(viewSource, /sortBy/)
  assert.match(tableSource, /仅上涨/)
  assert.match(tableSource, /仅有成本/)
  assert.match(tableSource, /monitor-table__mobile/)
  assert.match(viewSource, /el-drawer/)
  assert.match((await read('../src/components/monitor/MonitorInspector.vue')), /sparkline/)
})

test('监控检查器复用财务和 AI 的按需接口', () => {
  assert.match(viewSource, /getFinancialData/)
  assert.match(viewSource, /analyzeStock/)
  assert.match(viewSource, /financial-state/)
  assert.match(viewSource, /ai-advice/)
  assert.match(viewSource, /ai-error-message/)
})
