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

const storeSource = await readFile(new URL('../src/store/support.js', import.meta.url), 'utf8')

test('support store 只薄封装纯函数层,不含本地逻辑', () => {
  assert.match(storeSource, /defineStore\(\s*'support'/)
  assert.match(storeSource, /from\s+'\.\.\/utils\/supportPersistence'/)
  assert.match(storeSource, /from\s+'\.\.\/utils\/supportState'/)
  assert.ok(!storeSource.includes('stock_support_v1'), 'localStorage 键应只在 persistence 层出现')

  const api = [
    'likeIt', 'unlikeIt', 'takeAutoInvite',
    'suppressInvites', 'snoozeDays', 'liked', 'suppressed', 'snoozed',
  ]
  api.forEach((name) => {
    assert.ok(storeSource.includes(name), `store 应暴露 ${name}`)
  })
})

const layoutSource = await readFile(new URL('../src/components/Layout.vue', import.meta.url), 'utf8')
const footerSource = await readFile(new URL('../src/components/SiteFooter.vue', import.meta.url), 'utf8')

test('Layout 接入 SiteFooter 并启用 sticky-footer flex', () => {
  assert.match(layoutSource, /import\s+SiteFooter/)
  assert.match(layoutSource, /<SiteFooter\s*\/>|<\/SiteFooter>/)
  assert.match(layoutSource, /display:\s*flex/)
  assert.match(layoutSource, /min-height:\s*100dvh/)
  assert.match(layoutSource, /flex-direction:\s*column/)
})

test('SiteFooter 只放免责 + 一条静默增资入口,不动声量', () => {
  // 免责文案本体在 supportCopy(supportCopy 契约测试已锁);此处断言组件引用它
  assert.match(footerSource, /SUPPORT_COPY\.footerDisclaimer/)
  assert.match(footerSource, /SUPPORT_COPY\.footerSiteName/)
  assert.match(footerSource, /SUPPORT_COPY\.footerTipEntry/)
  assert.match(footerSource, /useSupportUi/)
  assert.match(footerSource, /TipSupportDialog/)
  const counts = (re) => (footerSource.match(re) || []).length
  assert.equal(counts(/SUPPORT_COPY\.footerTipEntry/g), 1, '页脚只有一个静默入口引用')
})

const commandBarSource = await readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8')

test('CommandBar 右簇接入 SupportButton', () => {
  assert.match(commandBarSource, /import\s+SupportButton\s+from\s+['"].*SupportButton\.vue['"]/)
  assert.match(commandBarSource, /<SupportButton\s*\/?>/)
})
