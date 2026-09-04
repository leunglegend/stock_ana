import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const SRC = resolve(fileURLToPath(new URL('.', import.meta.url)), '../src')

async function read(p) { return readFile(resolve(SRC, p), 'utf8') }

test('useUsMarket 用两条 useAsyncSection + SSE 摘要', async () => {
  const code = await read('composables/useUsMarket.js')
  assert.match(code, /useAsyncSection\(getUsSummary/)
  assert.match(code, /useAsyncSection\(getUsSectors/)
  assert.match(code, /getUsAiSummary\(/)
  assert.match(code, /closeAiSource|eventSource\.close/)
})

test('useUsMarket 导出摘要/榜单/AI 状态', async () => {
  const code = await read('composables/useUsMarket.js')
  for (const key of ['summarySection', 'sectorsSection', 'generateAiSummary']) {
    assert.match(code, new RegExp(key))
  }
})

test('useUsMarket AI 分块过滤 📊/🤖 开场帧并把 ❌ 记为错误', async () => {
  const code = await read('composables/useUsMarket.js')
  assert.match(code, /startsWith\('📊'\)/)
  assert.match(code, /startsWith\('🤖'\)/)
  assert.match(code, /startsWith\('❌'\)/)
  assert.match(code, /aiError\.value = true/)
})

test('useUsCard 只消费 summary 接口', async () => {
  const code = await read('composables/useUsCard.js')
  assert.match(code, /useAsyncSection\(getUsSummary/)
  assert.doesNotMatch(code, /getUsSectors/)
})

test('UsMarket 页面骨架 = workbench-page + 摘要带 + 主从 grid', async () => {
  const code = await read('views/UsMarket.vue')
  assert.match(code, /class="us-market-page workbench-page/)
  assert.match(code, /UsIndexStrip/)
  assert.match(code, /UsAiBand|MarketAiSummary/)
  assert.match(code, /UsSectorTable/)
  assert.match(code, /UsSectorDetailPanel/)
  assert.match(code, /data-page-title/)
})

test('UsMarket 页面不出现分页/搜索控件', async () => {
  const code = await read('views/UsMarket.vue')
  assert.doesNotMatch(code, /el-pagination/)
  assert.doesNotMatch(code, /el-input/)
  assert.doesNotMatch(code, /el-select/)
})

test('UsMarket 支持 ?sector= 深链还原', async () => {
  const code = await read('views/UsMarket.vue')
  assert.match(code, /route\.query\.sector|query\.sector/)
  assert.match(code, /getUsSectorStocks/)
})
