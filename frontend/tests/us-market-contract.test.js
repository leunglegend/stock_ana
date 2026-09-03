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

test('useUsCard 只消费 summary 接口', async () => {
  const code = await read('composables/useUsCard.js')
  assert.match(code, /useAsyncSection\(getUsSummary/)
  assert.doesNotMatch(code, /getUsSectors/)
})
