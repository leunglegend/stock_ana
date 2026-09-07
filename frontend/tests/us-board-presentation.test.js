import assert from 'node:assert/strict'
import test from 'node:test'
import { readFile } from 'node:fs/promises'

const read = (path) => readFile(new URL(`../src/${path}`, import.meta.url), 'utf8')

test('美股列表和详情复用 A 股展示组件，避免独立样式漂移', async () => {
  assert.match(await read('components/us/UsSectorTable.vue'), /<BoardTable/)
  assert.match(await read('components/us/UsSectorDetailPanel.vue'), /<BoardDetailPanel/)
})

test('美股板块面板有独立列表容器，详情变高不会撑开列表标题', async () => {
  const page = await read('views/UsMarket.vue')
  assert.match(page, /<div class="us-market-page__list">\s*<UsSectorTable/)
  assert.doesNotMatch(page, /\.us-market-page__sectors\s*\{[^}]*display: grid/)
})

test('同页板块切换不会将焦点和滚动位置移回页面标题', async () => {
  const router = await read('router/index.js')
  assert.match(router, /if \(to\.path === from\.path\) return/)
})
