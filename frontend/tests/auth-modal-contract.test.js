import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const source = await readFile(new URL('../src/components/LoginModal.vue', import.meta.url), 'utf8')

test('auth dialog exposes the approved signal/panel structure and copy', () => {
  for (const token of [
    'class="auth-dialog"',
    'auth-dialog__signal',
    'auth-dialog__panel',
    '把每一次登录，变成研究开始',
    '继续你的市场研究',
    '创建研究账户',
  ]) {
    assert.ok(source.includes(token), `missing ${token}`)
  }
})

test('auth dialog keeps behavior hooks for validation, keyboard submit and focus recovery', () => {
  for (const token of [
    'ref="loginFormRef"',
    'ref="registerFormRef"',
    '@keyup.enter="handleLogin"',
    '@keyup.enter="handleRegister"',
    'focusFirstInvalid',
    'focusLoginRecoveryField',
  ]) {
    assert.ok(source.includes(token), `missing ${token}`)
  }
})

test('auth dialog keeps pending-route and focus restoration behavior hooks', () => {
  for (const token of [
    'pendingRoute',
    'setPendingRoute',
    'consumePendingRoute',
    'lastActiveElement',
    'handleClosed',
  ]) {
    assert.ok(source.includes(token), `missing ${token}`)
  }
})

test('auth dialog includes responsive and accessible form styling contracts', () => {
  for (const token of [
    '@media (max-width: 640px)',
    'min-height: 44px',
    'label-position="top"',
    'grid-template-columns: 44% 56%',
    ':global(.auth-dialog .el-dialog__body)',
    ':global(.auth-dialog .el-dialog__header)',
    'el-dialog__headerbtn',
    'focus-visible',
    'prefers-reduced-motion',
    '--surface-sidebar',
    '--surface-primary',
    '--color-primary-500',
    '--color-warning-500',
    '注册后即可同步保存你的自选与研究报告。',
  ]) {
    assert.ok(source.includes(token), `missing ${token}`)
  }
})
