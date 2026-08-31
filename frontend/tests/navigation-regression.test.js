import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const read = (path) => readFile(new URL(path, import.meta.url), 'utf8')
const [layout, elementPlus, sidebar, router, reportDetail, reports] = await Promise.all([
  read('../src/components/Layout.vue'),
  read('../src/plugins/elementPlus.js'),
  read('../src/components/app/DesktopSidebar.vue'),
  read('../src/router/index.js'),
  read('../src/views/ReportDetail.vue'),
  read('../src/views/Reports.vue'),
])

function navIcons(source) {
  return [...source.matchAll(/path:\s*['"][^'"]+['"][^\n]*icon:\s*['"]([^'"]+)['"]/g)]
    .map((match) => match[1])
}

test('桌面菜单图标唯一且全部由 Element Plus 全局注册', () => {
  const icons = navIcons(layout)
  assert.ok(icons.length >= 8, '导航入口数量异常')
  assert.equal(new Set(icons).size, icons.length, `导航图标不应重复：${icons.join(', ')}`)

  const registry = elementPlus.match(/const icons = \{([\s\S]*?)\n\s*\}/)?.[1] || ''
  for (const icon of icons) {
    assert.match(registry, new RegExp(`\\b${icon}\\b`), `${icon} 未加入全局图标注册表`)
  }
})

test('桌面侧栏固定在视口且不产生自身滚动', () => {
  assert.match(sidebar, /position:\s*fixed/)
  assert.match(sidebar, /top:\s*0/)
  assert.match(sidebar, /left:\s*0/)
  assert.match(sidebar, /height:\s*100dvh/)
  assert.match(sidebar, /overflow:\s*hidden/)
})

test('报告详情入口具备真实视图，列表行跳转动态详情', () => {
  assert.match(router, /path:\s*['"]\/reports\/:id['"][\s\S]*?component:\s*\(\)\s*=>\s*import\(['"]\.\.\/views\/ReportDetail\.vue['"]\)/)
  assert.match(reportDetail, /reportApi\.getDetail\(route\.params\.id\)/)
  assert.match(reports, /router\.push\(\\?`\/reports\/\$\{report\.id\}`\\?\)/)
})
