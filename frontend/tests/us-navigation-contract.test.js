import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const SRC = resolve(fileURLToPath(new URL('.', import.meta.url)), '../src')
const read = (p) => readFile(resolve(SRC, p), 'utf8')

test('router 注册 /us 美股复盘路由', async () => {
  const code = await read('router/index.js')
  assert.match(code, /path: '\/us'/)
  assert.match(code, /UsMarket|views\/UsMarket\.vue/)
  assert.match(code, /title: '美股复盘'/)
})

test('Layout navBlueprint 含美股且 icon=Globe', async () => {
  const code = await read('components/Layout.vue')
  assert.match(code, /path: '\/us'/)
  assert.match(code, /title: '美股'/)
  assert.match(code, /icon: 'Globe'/)
})

test('Globe 图标注册进 elementPlus 白名单', async () => {
  const code = await read('plugins/elementPlus.js')
  assert.match(code, /Globe/)
})

test('侧栏与移动导航支持 /us 前缀高亮', async () => {
  const [desk, mob] = await Promise.all([
    read('components/app/DesktopSidebar.vue'),
    read('components/app/MobileNav.vue'),
  ])
  assert.match(desk, /us/)
  assert.match(mob, /us/)
})

test('Dashboard 接入 UsSnapshotCard', async () => {
  const dash = await read('views/Dashboard.vue')
  assert.match(dash, /UsSnapshotCard/)
  assert.match(dash, /useUsCard/)
})
