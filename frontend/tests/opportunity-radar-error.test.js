import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const radarUtils = await import('../src/utils/opportunityRadar.js')

test('机会雷达把原生 Error 规范成布尔/字符串而不是透传 Error 实例', () => {
  assert.equal(radarUtils.normalizeRadarError(new Error('板块加载失败')), true)
  assert.equal(radarUtils.normalizeRadarError('已是最新数据'), '已是最新数据')
  assert.equal(radarUtils.normalizeRadarError(null), false)
  assert.equal(radarUtils.normalizeRadarError(false), false)
})

test('机会雷达页面错误 prop 只接布尔或字符串，组合式函数不再直接存 Error', async () => {
  const [view, composable] = await Promise.all([
    readFile(new URL('../src/views/OpportunityRadar.vue', import.meta.url), 'utf8'),
    readFile(new URL('../src/composables/useOpportunityRadar.js', import.meta.url), 'utf8'),
  ])

  assert.match(view, /:error="boardsError"/)
  assert.match(view, /:error="stocksError"/)
  assert.doesNotMatch(composable, /record\.error\s*=\s*error/)
  assert.doesNotMatch(composable, /stockState\.error\s*=\s*error/)
  assert.match(composable, /record\.error\s*=\s*normalizeRadarError\(error\)/)
  assert.match(composable, /stockState\.error\s*=\s*normalizeRadarError\(error\)/)
})
