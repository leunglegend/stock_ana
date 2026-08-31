import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [layout, sidebar, mobileNav, commandBar, router] = await Promise.all([
  readFile(new URL('../src/components/Layout.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/DesktopSidebar.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/MobileNav.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/router/index.js', import.meta.url), 'utf8'),
])

test('Shell 提供视觉稿中的八项导航与正确的动态入口', () => {
  ;['市场', '板块', '雷达', '自选', '个股', '搜索', '报告', '报告详情'].forEach((title) => {
    assert.match(layout, new RegExp(`title: '${title}'`))
  })
  assert.match(layout, /path: '\/stock\/600519'/)
  assert.match(layout, /path: '\/reports\/latest'/)
  assert.match(sidebar, /XG/)
  assert.match(sidebar, /析股研究台/)
  assert.match(sidebar, /研究工作区/)
  assert.match(sidebar, /交易日 · 盘后/)
  assert.match(sidebar, /行情状态：数据正常/)
})

test('报告详情入口在动态详情路由前解析最近已完成报告', () => {
  const latestIndex = router.indexOf("path: '/reports/latest'")
  const detailIndex = router.indexOf("path: '/reports/:id'")

  assert.ok(latestIndex >= 0 && latestIndex < detailIndex)
  assert.match(router, /beforeEnter: async \(\) => \{[\s\S]*reportApi\.getList/)
  assert.match(router, /status === 'completed'/)
  assert.match(router, /return \{ name: 'ReportDetail', params: \{ id: latestReport\.id \} \}/)
  assert.match(router, /return \{ path: '\/reports' \}/)
})

test('桌面工具栏与移动标签严格映射视觉稿的区域关系', () => {
  assert.match(commandBar, /command-bar__date/)
  assert.match(commandBar, /盘后/)
  assert.match(commandBar, /数据正常/)
  assert.match(commandBar, /command-bar__search/)
  assert.match(commandBar, /grid-template-columns: minmax\(220px, 1fr\) minmax\(240px, 320px\) minmax\(220px, 1fr\)/)
  assert.match(layout, /<MobileNav v-if="isMobile" :items="navItems" \/>/)
  assert.ok(layout.indexOf('<MobileNav v-if="isMobile"') < layout.indexOf('<main class="app-shell__content">'))
  assert.match(mobileNav, /min-height: 42px/)
  assert.match(mobileNav, /overflow-x: auto/)
  assert.doesNotMatch(mobileNav, /position: fixed/)
  assert.doesNotMatch(layout, /72px \+ env\(safe-area-inset-bottom\)/)
})

test('报告、详情和个股导航激活态互不吞并，Shell 文件不超过 300 行', () => {
  assert.match(sidebar, /item\.id === 'reports'/)
  assert.match(sidebar, /item\.id === 'report-detail'/)
  assert.match(sidebar, /item\.id === 'stock'/)
  assert.match(mobileNav, /item\.id === 'reports'/)
  assert.match(mobileNav, /item\.id === 'report-detail'/)
  assert.match(mobileNav, /item\.id === 'stock'/)
  ;[layout, sidebar, mobileNav, commandBar, router].forEach((source) => {
    assert.ok(source.split('\n').length <= 300)
  })
})
