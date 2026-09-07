import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const SRC = resolve(fileURLToPath(new URL('.', import.meta.url)), '../src')

async function readApi() {
  return readFile(resolve(SRC, 'api/us.js'), 'utf8')
}

test('api/us.js 导出四个美股接口函数', async () => {
  const code = await readApi()
  for (const fn of ['getUsSummary', 'getUsSectors', 'getUsSectorStocks', 'getUsAiSummary']) {
    assert.match(code, new RegExp(`export (async )?function ${fn}|export const ${fn}`))
  }
})

test('REST 接口路径与返回约定', async () => {
  const code = await readApi()
  assert.match(code, /\/us\/summary/)
  assert.match(code, /\/us\/sectors/)
  assert.match(code, /sectors\/\$\{name\}|sectors\/\$\{encodeURIComponent/)
  assert.match(code, /encodeURIComponent/)
  assert.match(code, /\.then\(res => res\.data\)/)
})

test('SSE 封装遵循 [DONE] 与 EventSource 约定', async () => {
  const code = await readApi()
  assert.match(code, /EventSource\(/)
  assert.match(code, /\/us\/ai-summary/)
  assert.match(code, /'\[DONE\]'|"\[DONE\]"/)
  assert.match(code, /eventSource\.close\(\)/)
  assert.match(code, /return eventSource/)
})
