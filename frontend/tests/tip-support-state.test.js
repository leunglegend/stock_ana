import assert from 'node:assert/strict'
import test from 'node:test'
import {
  DEFAULT_SUPPORT,
  like,
  unlike,
  canAutoShowInvite,
  recordAutoInviteShown,
  setInviteSuppressed,
  setSnoozed,
  isSnoozed,
} from '../src/utils/supportState.js'
import { loadSupportLocal, saveSupportLocal } from '../src/utils/supportPersistence.js'

const DAY = 24 * 60 * 60 * 1000

function baseTime() {
  return new Date(2026, 8, 4, 12, 0, 0).getTime()
}

test('DEFAULT_SUPPORT 是未点亮、未关闭的干净态', () => {
  assert.equal(DEFAULT_SUPPORT.version, 1)
  assert.equal(DEFAULT_SUPPORT.liked, false)
  assert.equal(DEFAULT_SUPPORT.suppressInvite, false)
  assert.equal(DEFAULT_SUPPORT.snoozedUntil, null)
})

test('like/unlike 返回新对象且幂等', () => {
  const liked = like(DEFAULT_SUPPORT, baseTime())
  assert.equal(liked.liked, true)
  assert.equal(liked.likedAt, baseTime())
  assert.notEqual(liked, DEFAULT_SUPPORT)
  assert.equal(like(liked, baseTime()), liked, '已点亮时再 like 应原样返回')

  const back = unlike(liked)
  assert.equal(back.liked, false)
  assert.equal(back.likedAt, null)
  assert.equal(unlike(back), back, '已撤回时再 unlike 应原样返回')
})

test('canAutoShowInvite:默认放行;永久关闭/满 3 次/同天 1 次后不放行', () => {
  const t = baseTime()
  assert.equal(canAutoShowInvite(DEFAULT_SUPPORT, t), true)

  const suppressed = setInviteSuppressed(DEFAULT_SUPPORT)
  assert.equal(canAutoShowInvite(suppressed, t), false)

  let s = DEFAULT_SUPPORT
  for (let i = 0; i < 3; i += 1) s = recordAutoInviteShown(s, t + i * 1000)
  assert.equal(s.inviteAutoShown, 3)
  assert.equal(canAutoShowInvite(s, t + 5000), false, '满 3 次后当天不放行')

  assert.equal(canAutoShowInvite(recordAutoInviteShown(DEFAULT_SUPPORT, t), t + 1000), false, '同一天只 1 次')
  assert.equal(canAutoShowInvite(recordAutoInviteShown(DEFAULT_SUPPORT, t), t + DAY + 1000), true, '次日恢复')
})

test('recordAutoInviteShown 自增并更新时间戳', () => {
  const next = recordAutoInviteShown(DEFAULT_SUPPORT, baseTime())
  assert.equal(next.inviteAutoShown, 1)
  assert.equal(next.lastInviteAt, baseTime())
})

test('setSnoozed / isSnoozed 处理 30 天隐身边界', () => {
  const t = baseTime()
  const snoozed = setSnoozed(DEFAULT_SUPPORT, t + 30 * DAY)
  assert.equal(isSnoozed(snoozed, t), true, '期间隐身')
  assert.equal(isSnoozed(snoozed, t + 30 * DAY + 1), false, '到期即恢复')
  assert.equal(isSnoozed(DEFAULT_SUPPORT, t), false, '未设置不隐身')
})

test('持久化:空/坏数据回退默认;round-trip;老结构合并默认', async () => {
  const store = new Map()
  const errors = []
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => { store.set(k, String(v)) },
    removeItem: (k) => { store.delete(k) },
  }
  const origError = console.error
  console.error = (...args) => { errors.push(args) }

  try {
    assert.deepEqual(loadSupportLocal(), DEFAULT_SUPPORT, '无数据回退默认')

    const partial = { liked: true, likedAt: baseTime() }
    saveSupportLocal(partial)
    const loaded = loadSupportLocal()
    assert.equal(loaded.liked, true)
    assert.equal(loaded.suppressInvite, false, '缺省字段用默认值补齐')
    assert.equal(loaded.version, DEFAULT_SUPPORT.version)

    store.set('stock_support_v1', 'not-json{')
    assert.deepEqual(loadSupportLocal(), DEFAULT_SUPPORT, '坏 JSON 回退默认')
    assert.ok(errors.length > 0, '坏数据应 console.error')
  } finally {
    console.error = origError
    delete globalThis.localStorage
  }
})
