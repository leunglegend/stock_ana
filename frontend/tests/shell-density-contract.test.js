import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [layoutSource, commandBarSource, utilitiesSource, sidebarSource, mobileNavSource, searchSource] = await Promise.all([
  readFile(new URL('../src/components/Layout.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/CommandBarUtilities.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/DesktopSidebar.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/app/MobileNav.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/components/GlobalSearch.vue', import.meta.url), 'utf8'),
])

test('Shell 为机会雷达保留主导航入口，并在平板以下使用抽屉', () => {
  assert.match(layoutSource, /\{ path: '\/radar', title: '雷达', icon: 'TrendCharts' \}/)
  assert.match(layoutSource, /if \(path === '\/radar'\) return 'radar'/)
  assert.match(layoutSource, /<DesktopSidebar v-if="isDesktop"/)
  assert.match(layoutSource, /:show-menu-button="!isDesktop"/)
  assert.match(layoutSource, /<MobileNav v-if="isMobile"/)
})

test('桌面侧栏在中等桌面收敛为 64px 图标轨', () => {
  assert.match(sidebarSource, /@media \(min-width: 1024px\) and \(max-width: 1279px\)/)
  assert.match(sidebarSource, /width: 64px/)
  ;['desktop-sidebar__brand-copy', 'desktop-sidebar__link span', 'desktop-sidebar__label', 'desktop-sidebar__status'].forEach((selector) => {
    assert.match(sidebarSource, new RegExp(`\\.${selector.replace(' ', '\\s+')}[\\s\\S]*?display: none`))
  })
})

test('命令栏是连续工具条，手机仅保留高频入口与更多菜单', () => {
  assert.match(commandBarSource, /<CommandBarUtilities \/>/)
  assert.match(utilitiesSource, /class="command-utilities__more"/)
  assert.match(utilitiesSource, /\.command-utilities__theme\s*\{\s*display:\s*inline-flex/)
  assert.match(utilitiesSource, /:command="`theme:\$\{theme\.key\}`"/)
  assert.match(utilitiesSource, /@media \(max-width: 767px\)[\s\S]*\.command-utilities__account\s*\{\s*display:\s*none/)
  assert.match(utilitiesSource, /\.command-utilities__more\s*\{\s*display:\s*inline-flex/)
  assert.doesNotMatch(commandBarSource, /\.command-bar\s*\{[^}]*border-radius:/)
  assert.doesNotMatch(commandBarSource, /\.command-bar\s*\{[^}]*backdrop-filter:/)
})

test('移动导航与搜索浮层不残留固定蓝色，导航不使用磨砂背景', () => {
  assert.doesNotMatch(mobileNavSource, /rgba\(/)
  assert.doesNotMatch(mobileNavSource, /backdrop-filter/)
  assert.match(mobileNavSource, /background: var\(--surface-canvas\)/)
  assert.doesNotMatch(searchSource, /rgba\(60,\s*120,\s*216/)
  assert.match(searchSource, /background: var\(--surface-panel-muted\)/)
})
