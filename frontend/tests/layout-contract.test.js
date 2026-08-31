import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const styleSource = await readFile(new URL('../src/style.css', import.meta.url), 'utf8')
const viewNames = [
  'Dashboard',
  'BoardMonitor',
  'OpportunityRadar',
  'Watchlist',
  'StockDetail',
  'Search',
  'Reports',
  'ReportDetail',
]

const viewSources = await Promise.all(viewNames.map(async (name) => ({
  name,
  source: await readFile(new URL(`../src/views/${name}.vue`, import.meta.url), 'utf8'),
})))

test('全局样式提供均衡研究台布局契约', () => {
  assert.match(styleSource, /\.workbench-page\s*\{/)
  assert.match(styleSource, /\.workbench-page__header\s*\{/)
  assert.match(styleSource, /\.workbench-grid\s*\{/)
  assert.match(styleSource, /\.workbench-grid--primary\s*\{/)
  assert.match(styleSource, /@media\s*\(max-width:\s*767px\)/)
  assert.match(styleSource, /@media\s*\(min-width:\s*1024px\)\s*and\s*\(max-width:\s*1279px\)/)
  assert.match(styleSource, /@media\s*\(min-width:\s*768px\)\s*and\s*\(max-width:\s*1023px\)/)
})

test('主要页面接入统一工作台根容器', () => {
  viewSources.forEach(({ name, source }) => {
    assert.match(source, /class="[^"]*workbench-page/, `${name} 缺少 workbench-page`)
  })
})

test('主要页面接入统一紧凑页头', () => {
  viewSources.forEach(({ name, source }) => {
    const headerContract = name === 'StockDetail'
      ? /class="[^"]*stock-detail-page__identity-band/
      : /class="[^"]*workbench-page__header/
    assert.match(source, headerContract, `${name} 缺少 v1 页面身份带`)
  })
})
