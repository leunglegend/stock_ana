import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const dashboard = await readFile(new URL('../src/views/Dashboard.vue', import.meta.url), 'utf8')
const dashboardMarket = await readFile(new URL('../src/composables/useDashboardMarket.js', import.meta.url), 'utf8')
const boardMonitor = await readFile(new URL('../src/views/BoardMonitor.vue', import.meta.url), 'utf8')

test('Dashboard 通过顶层 computed 向模板暴露异步状态', () => {
  assert.match(dashboard, /useDashboardMarket/)
  assert.match(dashboardMarket, /summaryData: computed\(\(\) => summarySection\.data\.value\)/)
  assert.match(dashboard, /:summary="summaryData \|\| \{\}"/)
  assert.doesNotMatch(dashboard, /:summary="summarySection\.data/)
})

test('BoardMonitor 模板不重复读取自动解包 Ref 的 value', () => {
  const template = boardMonitor.match(/<template>([\s\S]*?)<\/template>/)?.[1] || ''
  assert.doesNotMatch(template, /(?:activeSection\.isLoading|isMobile)\.value/)
})
