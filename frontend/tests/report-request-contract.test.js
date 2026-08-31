import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [reports, reportDetail] = await Promise.all([
  readFile(new URL('../src/views/Reports.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/views/ReportDetail.vue', import.meta.url), 'utf8'),
])

test('报告列表只接受最后一次请求的结果', () => {
  assert.match(reports, /let listRequestId = 0/)
  assert.match(reports, /const requestId = \+\+listRequestId/)
  assert.match(reports, /if \(requestId !== listRequestId\) return/)
})

test('报告详情随路由参数切换加载，并忽略旧请求结果', () => {
  assert.match(reportDetail, /let detailRequestId = 0/)
  assert.match(reportDetail, /const requestId = \+\+detailRequestId/)
  assert.match(reportDetail, /if \(requestId !== detailRequestId\) return/)
  assert.match(reportDetail, /watch\(\(\) => route\.params\.id, loadReport, \{ immediate: true \}\)/)
})

test('生成中的报告不会重复启动轮询', () => {
  assert.match(reports, /if \(generating\.value \|\| pollingId\) return/)
})

test('报告列表使用真实状态和日期范围筛选，并在筛选后回到第一页', () => {
  assert.match(reports, /const statusFilter = ref\('all'\)/)
  assert.match(reports, /const daysFilter = ref\('30'\)/)
  assert.match(reports, /status: statusFilter\.value/)
  assert.match(reports, /days: daysFilter\.value/)
  assert.match(reports, /watch\(\[statusFilter, daysFilter\], \(\) => \{\s*page\.value = 1/)
})

test('报告桌面端在工具栏和表格底部都提供紧凑分页', () => {
  assert.equal((reports.match(/<el-pagination/g) || []).length, 2)
  assert.match(reports, /reports-page__toolbar-left/)
  assert.match(reports, /reports-page__pagination--top/)
})
