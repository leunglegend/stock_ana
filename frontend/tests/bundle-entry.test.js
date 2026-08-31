import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const mainSource = await readFile(new URL('../src/main.js', import.meta.url), 'utf8')
const chartSource = await readFile(new URL('../src/components/KLineChart.vue', import.meta.url), 'utf8')

test('公共入口不加载全量 UI 库和图表依赖', () => {
  assert.doesNotMatch(mainSource, /import ElementPlus from ['"]element-plus['"]/) 
  assert.doesNotMatch(mainSource, /element-plus\/dist\/index\.css/)
  assert.doesNotMatch(mainSource, /import \* as ElementPlusIconsVue/)
  assert.doesNotMatch(mainSource, /from ['"](?:vue-echarts|echarts\/)/)
})

test('ECharts 仅由 K 线组件按路由加载', () => {
  assert.match(chartSource, /from ['"]vue-echarts['"]/) 
  assert.match(chartSource, /from ['"]echarts\/core['"]/) 
})
