import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const copyPath = '../src/components/support/supportCopy.js'
const copySource = await readFile(new URL(copyPath, import.meta.url), 'utf8')

const FORBIDDEN = ['募捐', '慈善', '公益', '后台会看到', '保本', '稳赚', '翻倍']
// 注:「不构成任何收益承诺」是合规否认句(mustHave 锁定),故收益承诺不整体禁用

test('supportCopy 不含红线措辞', () => {
  FORBIDDEN.forEach((word) => {
    assert.ok(!copySource.includes(word), `文案不得出现「${word}」`)
  })
})

test('supportCopy 织入关键合规/诚实边界', () => {
  const mustHave = [
    '未成年人',           // 不诱导未成年人
    '戏称',               // 股东梗澄清
    '不构成任何收益承诺',  // 或同级否认收益(若改写需同步改这里)
    '收款记录',           // 集体致谢,非「后台看到每一笔」
    '量力增资',           // 金额随缘提醒
    '股东可顺手增资',     // 页脚静默入口文案
    '不构成任何投资建议', // 页脚免责
  ]
  mustHave.forEach((word) => {
    assert.ok(copySource.includes(word), `文案应包含「${word}」`)
  })
})

test('tokens.css 提供 --color-support-* 专属别名', async () => {
  const tokens = await readFile(new URL('../src/styles/tokens.css', import.meta.url), 'utf8')
  assert.match(tokens, /--color-support-50:\s*var\(--color-warning-50\)/)
  assert.match(tokens, /--color-support-500:\s*var\(--color-warning-500\)/)
  assert.match(tokens, /--color-support:\s*var\(--color-support-500\)/)
})
