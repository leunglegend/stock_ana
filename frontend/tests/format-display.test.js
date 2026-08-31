import assert from 'node:assert/strict'
import test from 'node:test'

import { isDisplayValueMissing } from '../src/utils/format.js'

test('格式化后的金额字符串不是缺失值', () => {
  assert.equal(isDisplayValueMissing('2.12万'), false)
  assert.equal(isDisplayValueMissing('21177.33亿'), false)
})

test('空值与空字符串仍视为缺失值', () => {
  assert.equal(isDisplayValueMissing(null), true)
  assert.equal(isDisplayValueMissing(undefined), true)
  assert.equal(isDisplayValueMissing('  '), true)
  assert.equal(isDisplayValueMissing(0), false)
})
