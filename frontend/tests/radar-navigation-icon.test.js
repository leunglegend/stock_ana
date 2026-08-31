import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const layoutPath = resolve(process.cwd(), 'src/components/Layout.vue')
const pluginPath = resolve(process.cwd(), 'src/plugins/elementPlus.js')

test('雷达导航图标在 Layout 配置与 Element Plus 插件注册中保持一致', async () => {
  const [layoutSource, pluginSource] = await Promise.all([
    readFile(layoutPath, 'utf8'),
    readFile(pluginPath, 'utf8'),
  ])

  assert.match(
    layoutSource,
    /path:\s*'\/radar'[\s\S]*icon:\s*'TrendCharts'/,
    'Layout 雷达导航应继续使用 TrendCharts 图标',
  )
  assert.match(
    pluginSource,
    /import\s*\{[\s\S]*\bTrendCharts\b[\s\S]*\}\s*from '@element-plus\/icons-vue'/,
    'elementPlus.js 应导入 TrendCharts 图标',
  )
  assert.match(
    pluginSource,
    /const\s+icons\s*=\s*\{[\s\S]*\bTrendCharts\b[\s\S]*\}/,
    'elementPlus.js 应在 icons 注册表中包含 TrendCharts',
  )
  assert.match(
    pluginSource,
    /Object\.entries\(icons\)\.forEach\(\(\[name,\s*component\]\)\s*=>\s*app\.component\(name,\s*component\)\)/,
    'installElementPlus 应通过 icons 注册表全局注册图标组件',
  )
})
