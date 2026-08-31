import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [tokens, styles, elementPlus, panel, layout, commandBar, sidebar, utilities, globalSearch] = await Promise.all([
  readFile(new URL('../src/styles/tokens.css', import.meta.url), 'utf8'),
  readFile(new URL('../src/style.css', import.meta.url), 'utf8'),
  readFile(new URL('../src/styles/element-plus.css', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/base/SectionPanel.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/Layout.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/DesktopSidebar.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/CommandBarUtilities.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/GlobalSearch.vue', import.meta.url), 'utf8'),
])

test('v1 使用唯一的机构研究盘 Token', () => {
  assert.match(tokens, /--surface-page:\s*#f4f7fa/)
  assert.match(tokens, /--surface-canvas:\s*#ffffff/)
  assert.match(tokens, /--surface-panel-muted:\s*#eef2f6/)
  assert.match(tokens, /--surface-sidebar:\s*#172839/)
  assert.match(tokens, /--color-primary-500:\s*#2376a7/)
  assert.match(tokens, /--color-up-500:\s*#c83e39/)
  assert.match(tokens, /--color-down-500:\s*#18835b/)
  assert.match(tokens, /--radius-panel:\s*0/)
})

test('v1 固定机构研究盘密度', () => {
  assert.match(tokens, /--page-header-height:\s*44px/)
  assert.match(tokens, /--toolbar-height:\s*40px/)
  assert.match(tokens, /--command-bar-height:\s*40px/)
  assert.match(tokens, /--table-head-height:\s*32px/)
  assert.match(tokens, /--data-row-height:\s*40px/)
  assert.match(styles, /min-height:\s*var\(--page-header-height\)/)
  assert.match(commandBar, /min-height:\s*var\(--command-bar-height\)/)
})

test('常规工作面无圆角无阴影，只有浮层可提升', () => {
  assert.match(panel, /border:\s*1px solid var\(--border-default\)/)
  assert.match(panel, /border-radius:\s*0/)
  assert.match(panel, /box-shadow:\s*none/)
  assert.match(panel, /section-panel--overlay[\s\S]*box-shadow:\s*var\(--shadow-overlay\)/)
  assert.match(elementPlus, /\.el-card[\s\S]*border-radius:\s*0/)
  assert.match(elementPlus, /\.el-dialog,[\s\S]*box-shadow:\s*var\(--shadow-overlay\)/)
})

test('Shell 按 v1 的四档宽度降级', () => {
  assert.match(sidebar, /width:\s*168px/)
  assert.match(sidebar, /@media \(min-width: 1024px\) and \(max-width: 1279px\)/)
  assert.match(sidebar, /width:\s*64px/)
  assert.match(layout, /@media \(min-width: 768px\) and \(max-width: 1023px\)/)
  assert.match(layout, /@media \(max-width: 767px\)/)
})

test('主题入口保留桌面按钮并在移动端降级到更多菜单', () => {
  assert.match(commandBar, /<CommandBarUtilities\s*\/>/)
  assert.match(utilities, /\.command-utilities__theme\s*\{\s*display:\s*inline-flex/)
  assert.match(utilities, /\.command-utilities__theme\s*\{\s*display:\s*none/)
  assert.match(utilities, /:command="`theme:\$\{theme\.key\}`"/)
})

test('全局搜索只保留输入、状态与结果，不展示教学文案', () => {
  assert.doesNotMatch(globalSearch, /输入代码或名称，回车跳转完整搜索页或个股详情/)
  assert.doesNotMatch(globalSearch, /快捷键/)
  assert.doesNotMatch(globalSearch, /search-dialog__subtitle/)
  assert.doesNotMatch(globalSearch, /search-dialog__tips/)
  assert.doesNotMatch(globalSearch, /完整搜索/)
  assert.doesNotMatch(globalSearch, /search-dialog__full-search/)
})
