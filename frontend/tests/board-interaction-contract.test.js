import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { createRequestGate } from '../src/utils/opportunityRadar.js'

const boardMonitor = await readFile(new URL('../src/views/BoardMonitor.vue', import.meta.url), 'utf8')
const boardDetail = await readFile(new URL('../src/components/board/BoardDetailPanel.vue', import.meta.url), 'utf8')

function functionSource(source, name) {
  return source.match(new RegExp(`async function ${name}\\([^)]*\\) \\{([\\s\\S]*?)\\n\\}`))?.[1] || ''
}

test('切换板块类型会清理深链并保留用户选择的 Tab', () => {
  const handler = functionSource(boardMonitor, 'handleTabChange')

  assert.match(handler, /closeBoard\(false\)/)
  assert.match(handler, /await replaceRouteQuery\(tabName, ''\)/)
  assert.doesNotMatch(handler, /syncBoardFromRoute/)
  assert.match(boardMonitor, /query: \{ type, \.\.\.\(name \? \{ name \} : \{\}\) \}/)
})

test('旧板块请求完成后不会覆盖较新选择的深链', () => {
  const openBoard = functionSource(boardMonitor, 'openBoard')

  assert.match(openBoard, /selectedBoardType\.value === boardType/)
  assert.match(openBoard, /selectedBoard\.value\?\.name === boardName/)
})

test('快速切换深链时过期的路由同步不会覆盖新选择', () => {
  const syncBoard = functionSource(boardMonitor, 'syncBoardFromRoute')

  assert.match(boardMonitor, /let routeSyncGeneration = 0/)
  assert.match(boardMonitor, /function isCurrentRouteSync\(generation, key\)/)
  assert.match(syncBoard, /const syncGeneration = \+\+routeSyncGeneration/)
  assert.match(syncBoard, /await loadBoards\(type\)\n\s*if \(!isCurrentRouteSync\(syncGeneration, syncKey\)\) return/)
  assert.match(syncBoard, /await reloadBoardStocks\(\)\n\s*if \(!isCurrentRouteSync\(syncGeneration, syncKey\)\) return/)
})

test('路由切换会在详情请求写入前使旧成分股结果失效', async () => {
  const gate = createRequestGate()
  let resolveFirst
  const firstToken = gate.next('detail-stocks')
  const firstRequest = new Promise((resolve) => { resolveFirst = resolve }).then((stocks) => {
    if (gate.isCurrent('detail-stocks', firstToken)) return stocks
    return null
  })
  const secondToken = gate.next('detail-stocks')

  resolveFirst([{ code: '000001' }])
  assert.equal(await firstRequest, null)
  assert.equal(gate.isCurrent('detail-stocks', secondToken), true)

  const syncBoard = functionSource(boardMonitor, 'syncBoardFromRoute')
  const reloadStocks = functionSource(boardMonitor, 'reloadBoardStocks')
  assert.ok(syncBoard.indexOf("detailRequestGate.invalidate('stocks')") < syncBoard.indexOf('await loadBoards(type)'))
  assert.match(reloadStocks, /const token = detailRequestGate\.next\('stocks'\)/)
  assert.match(reloadStocks, /if \(!detailRequestGate\.isCurrent\('stocks', token\)\) return\n\s*boardStocks\.value = stocks/)
})

test('移动端成分股指标使用带标签的稳定双列网格', () => {
  ;['换手率', 'PE', '市值', '价格\/涨跌'].forEach((label) => {
    assert.match(boardDetail, new RegExp(`board-detail__metric-label">${label}`))
  })
  assert.match(boardDetail, /grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/)
  assert.match(boardDetail, /\.board-detail__metric \{[^}]*min-width: 0/)
})
