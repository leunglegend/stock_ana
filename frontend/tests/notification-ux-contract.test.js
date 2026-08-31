import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const notificationBell = await readFile(
  new URL('../src/components/NotificationBell.vue', import.meta.url),
  'utf8',
)

test('通知按钮满足最小触控尺寸', () => {
  assert.match(notificationBell, /\.bell-icon-wrapper\s*\{[\s\S]*?width:\s*44px;/)
  assert.match(notificationBell, /\.bell-icon-wrapper\s*\{[\s\S]*?height:\s*44px;/)
})

test('通知菜单使用主题语义 Token 而不是固定浅色', () => {
  const style = notificationBell.match(/<style scoped>([\s\S]*?)<\/style>/)?.[1] || ''
  assert.match(style, /var\(--surface-panel\)/)
  assert.match(style, /var\(--text-primary\)/)
  assert.match(style, /var\(--border-subtle\)/)
  assert.doesNotMatch(style, /#[0-9a-fA-F]{3,8}\b/)
})
