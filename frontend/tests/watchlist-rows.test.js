import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { createServer } from 'vite'

let server
let createRowRequestVersionGate

before(async () => {
  server = await createServer({ server: { middlewareMode: true } })
  ;({ createRowRequestVersionGate } = await server.ssrLoadModule('/src/components/watchlist/useWatchlistRows.js'))
})

after(async () => {
  await server.close()
})

test('同一股票连续重试时仅最后一次请求版本仍可写入', () => {
  const gate = createRowRequestVersionGate()
  const firstRequest = gate.start('600519')
  const secondRequest = gate.start('600519')

  assert.equal(gate.isCurrent('600519', firstRequest), false)
  assert.equal(gate.isCurrent('600519', secondRequest), true)
})
