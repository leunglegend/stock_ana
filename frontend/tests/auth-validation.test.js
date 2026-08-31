import assert from 'node:assert/strict'
import test from 'node:test'

import { focusLoginRecoveryField } from '../src/utils/authValidation.js'

function focusTracker() {
  let calls = 0
  return {
    ref: { value: { focus: () => { calls += 1 } } },
    calls: () => calls,
  }
}

test('凭证错误且字段完整时聚焦密码以便快速修正', () => {
  const username = focusTracker()
  const password = focusTracker()

  focusLoginRecoveryField(
    { value: { username: 'qa-user', password: 'wrong-password' } },
    { usernameRef: username.ref, passwordRef: password.ref },
  )

  assert.equal(username.calls(), 0)
  assert.equal(password.calls(), 1)
})

test('缺失字段仍优先聚焦第一个待填写字段', () => {
  const username = focusTracker()
  const password = focusTracker()

  focusLoginRecoveryField(
    { value: { username: '', password: '' } },
    { usernameRef: username.ref, passwordRef: password.ref },
  )
  assert.equal(username.calls(), 1)

  focusLoginRecoveryField(
    { value: { username: 'qa-user', password: '' } },
    { usernameRef: username.ref, passwordRef: password.ref },
  )
  assert.equal(password.calls(), 1)
})
