# 点赞为股 · 打赏入口实施计划(A 方案合并版)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给「智能股票分析平台」加一个全站常驻的「点赞为股 → 顺带增资」入口(顶栏可点亮图标 + 页脚静默注脚),支持微信/支付宝个人收款码打赏,文案走「股东情怀(适度)」人设。

**Architecture:** 纯函数逻辑层(`supportState`/`supportPersistence`)与 Pinia store、展示组件分层;点不点亮、是否邀赏、是否隐身全部落在 localStorage(`stock_support_v1`),无后端、无商户 API、不伪造到账。顶栏 `SupportButton` 提供确认卡(自绘浮层),页脚 `SiteFooter` 提供合规注脚 + 静默增资入口,两者共用一个全屏打赏 `TipSupportDialog`。

**Tech Stack:** Vue 3(`<script setup>`)+ Element Plus(局部注册)+ Pinia(setup store)+ Vite;测试用 Node 内置 `node:test` + 源码契约断言(仓库无 vitest)。

**Spec:**
- `docs/design-rounds/2026-09-04-tip-pay/00-候选方案概览.md`(锁定前提)
- `docs/design-rounds/2026-09-04-tip-pay/01-方向一-页脚静默增资.md`
- `docs/design-rounds/2026-09-04-tip-pay/02-方向二-顶栏信仰充值.md`
- `docs/design-rounds/2026-09-04-tip-pay/03-方向三-点赞为股两段式.md`
- 拍板产物:`docs/design-rounds/2026-09-04-tip-pay/decision-brief.html`(用户选了 A = D3 两段式骨架 + 吸收 D2 的状态机 + 先落 D1 站级合规页脚;含 5 条动工前必改点)

## Global Constraints

逐条来自 Spec(执行时全部任务隐含遵守):
- **人设**:文案 = 股东情怀(适度)。用户=股东,打赏=「增资/投票」,只在文案与轻交互层面玩梗;**不做**金额档位/积分/排行榜/「N 人已赞」计数。
- **支付现实**:微信 + 支付宝**个人收款码**;**无后端资金流、无到账检测、无商户 API、无支付成功回调/提示**。作者随后把码图覆盖到 `src/assets/support/` 即可换码。
- **红线措辞**:不承诺收益/回报、不诱导未成年人、不把打赏说成投资、不得出现「募捐/慈善/公益」字眼;UI 永不显示计数(单浏览器计数是幻觉)。
- **股东梗澄清**:出现「股东/增资/表决权/募资」等词处,同一文案块内必须有「戏称、不构成股权/收益/治理权利」的澄清(打赏卡合规脚注 1-2 承担)。
- **诚实边界**:打赏致谢只说「会出现在作者收款记录 / 择日集体道谢」,不说「作者在后台会看到每一笔」;不要求用户截图回传。
- **状态真实**:点赞/隐身存 localStorage 单键 `stock_support_v1`,沿用 `stock_` 前缀 + 纯 load/save helper try/catch 模式(参考 `src/store/watchlistPersistence.js`)。
- **颜色语义**:红涨绿跌不变。点亮态用**专属别名 token** `--color-support-*`(当前映射到品牌金 `--color-warning-*`),形状用内联 SVG 拇指(与星形「自选」导航区隔);不直接改 EP 默认 amber。
- **技术红线**:不改后端、不加新依赖、不动 EP 全局注册(`el-popover`/`el-message` 未注册,禁用);`.vue` 一律 `<script setup>`;测试跑 `cd frontend && node --test tests/<file>.test.js`,门禁另有 `npm run build`。
- **仓库工作流**:分支 `feat/tip-pay-support` 上工作;每任务末提交;提交信息形如 `feat(tip): <summary>` / `test(tip): <summary>`。

## 仓库地形速览(所有路径以仓库根为准;根下才有 `frontend/ backend/ docs/`)

- 顶栏右簇插点:`frontend/src/components/app/CommandBar.vue:22-25`(`.command-bar__right` 内 `<NotificationBell />` 与 `<CommandBarUtilities />` 之间),模板与 `<script setup>` 各加一行。
- 布局:`frontend/src/components/Layout.vue`(注意**不在** `app/` 下,在 `components/Layout.vue`)。`<main class="app-shell__content">` 结束于 `:29`,页脚插在 `:29` 之后、`:30` 的 `</div>` 之前。CSS 见 `:90-99`(`.app-shell__main` 当前 `display` 未设为 flex)。
- tokens:插 `--color-support-*` 别名到 `frontend/src/styles/tokens.css:79`(`--color-success` 之后、`--surface-page` 之前)。
- store 范例:`frontend/src/store/watchlistPersistence.js`(纯 load/save try/catch)+ `frontend/src/store/user.js`(setup store 写法);`frontend/src/store/index.js` 负责 `pinia` 实例(不要动它)。
- 弹窗范例:`el-dialog` 已局部注册(`plugins/elementPlus.js:74`);NotificationBell 用 `el-dropdown` 承载自绘面板(本功能确认卡**不用** el-dropdown/el-popover,自绘浮层更可控)。
- 测试范例:Node 内置 `node:test`,`frontend/tests/*.test.js`,源码契约用 `readFile(new URL('../src/...', import.meta.url), 'utf8')`(见 `tests/layout-contract.test.js`)。测试**不能** import 含 `@/` 别名的模块(node 解析不了);store 用文本契约断言即可。
- 工具:`src/composables/useResponsive.js` 导出 `isMobile/isTablet/isDesktop`。
- icons:`@element-plus/icons-vue` 无 `ThumbsUp`(已核实)→ 用内联 SVG 拇指。

## 文件结构(本计划将创建/修改)

**新建:**
- `frontend/src/utils/supportState.js` — 纯函数:默认态 + 点赞/撤回/邀赏闸门/隐身转移。
- `frontend/src/utils/supportPersistence.js` — localStorage 存取(`stock_support_v1`)。
- `frontend/src/store/support.js` — Pinia setup store(薄封装,方法签名见 Task 1 接口)。
- `frontend/src/components/support/supportCopy.js` — 全部文案常量(集中改稿点)。
- `frontend/src/components/support/qrImages.js` — 双码图片接入点(当前 null → 作者覆盖后取消注释)。
- `frontend/src/components/support/useSupportUi.js` — 单例打赏卡可见性 ref。
- `frontend/src/components/support/TipSupportDialog.vue` — 全屏打赏卡(el-dialog)。
- `frontend/src/components/SiteFooter.vue` — 站级合规页脚 + 静默增资入口。
- `frontend/src/components/app/SupportButton.vue` — 顶栏点赞为股入口 + 自绘确认卡。
- `frontend/tests/tip-support-state.test.js` — 纯逻辑 + 持久化单测(node:test)。
- `frontend/tests/tip-support-contract.test.js` — 源码契约/合规词/接线断言。

**修改:**
- `frontend/src/styles/tokens.css` — 加 3 行 `--color-support-*` 别名(Task 2)。
- `frontend/src/components/Layout.vue` — 页脚接线 + sticky-footer flex 改造(Task 4)。
- `frontend/src/components/app/CommandBar.vue` — 插 `<SupportButton />`(Task 7)。

---

## Task 1: 纯函数逻辑层(点赞/邀赏闸门/隐身)+ 单测

先做无框架依赖的纯逻辑:仓库能跑真实单测的只有不碰 `@/` 别名、不 import `.vue` 的模块;闸门逻辑是全功能最该测的部分。

**Files:**
- Create: `frontend/src/utils/supportState.js`
- Create: `frontend/src/utils/supportPersistence.js`
- Test: `frontend/tests/tip-support-state.test.js`

**Interfaces:**
- Produces(供 Task 3 store、Task 6 SupportButton 使用,签名锁定):
  - `DEFAULT_SUPPORT` — 默认状态对象(浅拷贝时用展开)。
  - `like(state)` / `unlike(state)` → 返回**新**对象;幂等(无变化时返回原引用)。
  - `canAutoShowInvite(state, now = Date.now())` → boolean:被永久关闭 / 已邀 3 次 / 当天已邀过 → false。
  - `recordAutoInviteShown(state, now = Date.now())` → 计数 +1 并记 `lastInviteAt`。
  - `setInviteSuppressed(state)` → 置 `suppressInvite:true`。
  - `setSnoozed(state, untilTs)` / `isSnoozed(state, now = Date.now())`。
- Consumes:无(不 import 任何东西)。

- [ ] **Step 1: 写失败单测**

创建 `frontend/tests/tip-support-state.test.js`:

```js
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd frontend && node --test tests/tip-support-state.test.js`
Expected: FAIL —— import 报「Cannot find module '../src/utils/supportState.js'」。

- [ ] **Step 3: 实现纯函数层**

创建 `frontend/src/utils/supportState.js`:

```js
export const DEFAULT_SUPPORT = {
  version: 1,
  liked: false,
  likedAt: null,
  inviteAutoShown: 0,
  lastInviteAt: null,
  suppressInvite: false,
  snoozedUntil: null,
}

const AUTO_INVITE_LIMIT = 3

export function like(state, now = Date.now()) {
  if (state.liked) return state
  return { ...state, liked: true, likedAt: now }
}

export function unlike(state) {
  if (!state.liked) return state
  return { ...state, liked: false, likedAt: null }
}

function sameLocalDay(a, b) {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

export function canAutoShowInvite(state, now = Date.now()) {
  if (state.suppressInvite) return false
  if (state.inviteAutoShown >= AUTO_INVITE_LIMIT) return false
  if (state.lastInviteAt && sameLocalDay(new Date(state.lastInviteAt), new Date(now))) return false
  return true
}

export function recordAutoInviteShown(state, now = Date.now()) {
  return { ...state, inviteAutoShown: state.inviteAutoShown + 1, lastInviteAt: now }
}

export function setInviteSuppressed(state) {
  if (state.suppressInvite) return state
  return { ...state, suppressInvite: true }
}

export function setSnoozed(state, untilTs) {
  return { ...state, snoozedUntil: untilTs }
}

export function isSnoozed(state, now = Date.now()) {
  return !!(state.snoozedUntil && state.snoozedUntil > now)
}
```

创建 `frontend/src/utils/supportPersistence.js`:

```js
import { DEFAULT_SUPPORT } from './supportState'

const STORAGE_KEY = 'stock_support_v1'

export function loadSupportLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULT_SUPPORT }
    const parsed = JSON.parse(raw)
    return { ...DEFAULT_SUPPORT, ...parsed }
  } catch (error) {
    console.error('加载点赞/增资数据失败:', error)
    return { ...DEFAULT_SUPPORT }
  }
}

export function saveSupportLocal(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('保存点赞/增资数据失败:', error)
  }
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd frontend && node --test tests/tip-support-state.test.js`
Expected: PASS(全部绿色)。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/utils/supportState.js frontend/src/utils/supportPersistence.js frontend/tests/tip-support-state.test.js
git commit -m "feat(tip): 点赞为股纯函数层(状态机闸门 + stock_support_v1 持久化)"
```

---

## Task 2: tokens 别名 + 文案常量 + 合规契约测试

金点撞色 #1 的处理:加 `--color-support-*` 专属别名(现在指到品牌金),后续要换色只改这一处。文案全部收进 `supportCopy.js`,并新增一份**源码契约测试**,把红线措辞与关键文案钉死在测试里(仓库正是靠这种测试守住跨页面约定)。

**Files:**
- Modify: `frontend/src/styles/tokens.css:79`(在 `--color-success` 行后插入 3 行)
- Create: `frontend/src/components/support/supportCopy.js`
- Create: `frontend/src/components/support/qrImages.js`
- Test: `frontend/tests/tip-support-contract.test.js`

**Interfaces:**
- Produces: `SUPPORT_COPY`(字段名即文案槽,下方代码),`QR_IMAGES`(`{ wechat: string|null, alipay: string|null }`),CSS 变量 `--color-support-50 / --color-support-500 / --color-support`。
- Consumes:无。

- [ ] **Step 1: 先写合规契约测试(含红线段)**

创建 `frontend/tests/tip-support-contract.test.js`:

```js
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const copyPath = '../src/components/support/supportCopy.js'
const copySource = await readFile(new URL(copyPath, import.meta.url), 'utf8')

const FORBIDDEN = ['募捐', '慈善', '公益', '后台会看到', '收益承诺', '保本', '稳赚', '翻倍']

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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: FAIL —— `copySource` 读不到 `supportCopy.js`。

- [ ] **Step 3: 加 tokens 别名**

`frontend/src/styles/tokens.css`,在 `--color-success: var(--color-down-500);`(第 79 行)之后、`--surface-page` 之前插入:

```css
  /* 点赞为股 · 支持色别名:点亮态暂用品牌金,将来换独立色只改此处 */
  --color-support-50: var(--color-warning-50);
  --color-support-500: var(--color-warning-500);
  --color-support: var(--color-support-500);
```

- [ ] **Step 4: 实现文案常量与码图接入点**

创建 `frontend/src/components/support/supportCopy.js`:

```js
// 「点赞为股 · 打赏」全站文案集中改稿点。人设:股东情怀(适度)。
// 红线(勿删/勿改语义):无「募捐/慈善/公益」、无收益承诺、点醒未成年人、
// 「股东/增资」为戏称的澄清必须在场;致谢只说收款记录/集体道谢,不说「后台看到每一笔」。
export const SUPPORT_COPY = {
  // —— 顶栏入口 ——
  entryAriaLabel: '给析股研究台点赞',
  entryTitleIdle: '点赞:免费给研究台投一票,不伤本金',
  entryTitleLiked: '你已是本机股东 · 再点开股东卡',
  labelIdle: '点赞',
  labelLiked: '已一票',
  // —— 确认卡(点亮后) ——
  confirmHead: '表决成功。本机股东名册 +1。',
  confirmSub: '你持股『鼓励』1 股:行权价 0 元,不盯盘、不套牢、随时可撤。',
  confirmLocalNote: '此票记在本机浏览器:换设备或清缓存不随行——属彩蛋,不属实缴登记。',
  inviteLead: '这票研究员收下了。若哪天想让它更有分量:',
  inviteAction: '顺带增资?',
  inviteDecline: '先不了,白嫖也是股东权益。',
  inviteGhost: '想让它更有分量?顺带增资 →',
  revokeAction: '收回这一票',
  suppressAction: '以后别再提增资',
  snoozeAction: '暂时收起这个入口',
  revokeNote: '票已收回,研究台照常营业,欢迎随时再投。',
  // —— 打赏卡 ——
  dialogEyebrow: '股东增资 · 自愿支持',
  dialogHead: '研究不收费,服务器要养;各位股东,量力增资。',
  dialogSub: '析股研究台由一个人维护:行情、服务器、AI 的电费都自费。这笔钱不拿去扩产,只够请这个 AI 打工仔多喝几杯咖啡。',
  amountNote: '金额随缘:一杯奶茶区间(6.66 / 8.88 / 18.88)刚刚好;超过 99 请三思——这里不搞大额集资。',
  scanHint: '长按识别二维码,或用对应 App 扫一扫',
  qrWechatLabel: '微信',
  qrAlipayLabel: '支付宝',
  qrPlaceholder: '收款码占位:作者把图放进\nsrc/assets/support/ 并接线 qrImages.js',
  thanksCollective: '扫码即赠,无需截图回传;每一笔增资都会出现在作者的微信 / 支付宝收款记录里。作者会挑个交易日,在复盘里向全体股东集体道谢。',
  payeeMask: '收款方:析股台 · *哥(支付前请核对,认准这一行)',
  compliance1: '打赏是自愿赠与:非购买、非投资,不构成任何收益承诺,也不解锁任何功能。',
  compliance2: '本页「股东 / 增资 / 表决权」均为戏称,不构成任何股权、收益分配或公司治理权利。',
  compliance3: '未成年人请勿打赏——把零花钱先投资给自己,就是最好的复利。',
  actionPrimary: '继续看盘',
  actionLater: '下次一定',
  snoozedTip: '已收起 30 天。想回来?入口 30 天后自动复出。',
  // —— 页脚 ——
  footerSiteName: '析股研究台',
  footerDisclaimer: '数据仅供研究参考,不构成任何投资建议 · 内容不构成买卖依据',
  footerTipEntry: '股东可顺手增资 ↗',
  footerTipAria: '打开股东增资入口(打赏支持)',
}
```

创建 `frontend/src/components/support/qrImages.js`:

```js
// 作者接入个人收款码的唯一改点:
//   1) 把码图另存为 src/assets/support/wechat.png 与 alipay.png;
//   2) 取消下面两行 import 并把 QR_IMAGES.wechat / .alipay 指向它们。
// 当前保持 null:组件渲染占位卡,避免缺失图片导致 vite build 失败。
// import wechatImg from '@/assets/support/wechat.png'
// import alipayImg from '@/assets/support/alipay.png'

export const QR_IMAGES = {
  wechat: null,
  alipay: null,
}
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/styles/tokens.css frontend/src/components/support/supportCopy.js frontend/src/components/support/qrImages.js frontend/tests/tip-support-contract.test.js
git commit -m "feat(tip): 支持色别名 + 文案常量集中改稿点 + 红线契约测试"
```

---

## Task 3: Pinia store(薄封装)

把纯函数包成 setup store;store 保持零业务逻辑(逻辑都在 Task 1 已测),因此测试走**源码契约**(文本断言它调用 utils、不自己写 localStorage 字面量键、方法名齐全)。

**Files:**
- Create: `frontend/src/store/support.js`
- Test: `frontend/tests/tip-support-contract.test.js`(追加一节)

**Interfaces:**
- Consumes: Task 1 的 `loadSupportLocal/saveSupportLocal`、`like/unlike/canAutoShowInvite/recordAutoInviteShown/setInviteSuppressed/setSnoozed/isSnoozed`;`DEFAULT_SUPPORT`。
- Produces:`useSupportStore`(setup store),暴露:
  - ref `state`
  - computed `liked` / `suppressed` / `snoozed`
  - action `likeIt(): boolean`(返回是否真的发生了"未点亮→点亮")
  - action `unlikeIt(): void`
  - action `takeAutoInvite(): boolean`(闸门放行才 +1 并返回 true)
  - action `suppressInvites(): void`
  - action `snoozeDays(days = 30): void`
- 注:store 的 import 必须是**相对路径**(`../utils/...`),让契约测试可读源码;组件里仍可用 `@/store/support`。

- [ ] **Step 1: 先往契约测试追加 store 断言**

在 `frontend/tests/tip-support-contract.test.js` 追加(文件顶部已有 `readFile`,此处新读 store 源并加 test):

```js
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: FAIL —— store 文件不存在。

- [ ] **Step 3: 实现 store**

创建 `frontend/src/store/support.js`:

```js
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { loadSupportLocal, saveSupportLocal } from '../utils/supportPersistence'
import {
  DEFAULT_SUPPORT,
  canAutoShowInvite,
  isSnoozed,
  like,
  recordAutoInviteShown,
  setInviteSuppressed,
  setSnoozed,
  unlike,
} from '../utils/supportState'

export const useSupportStore = defineStore('support', () => {
  const state = ref(loadSupportLocal())

  const liked = computed(() => state.value.liked)
  const suppressed = computed(() => state.value.suppressInvite)
  const snoozed = computed(() => isSnoozed(state.value))

  function persist(next) {
    state.value = next
    saveSupportLocal(next)
  }

  function likeIt() {
    const next = like(state.value)
    if (next === state.value) return false
    persist(next)
    return true
  }

  function unlikeIt() {
    const next = unlike(state.value)
    if (next !== state.value) persist(next)
  }

  function takeAutoInvite() {
    if (!canAutoShowInvite(state.value)) return false
    persist(recordAutoInviteShown(state.value))
    return true
  }

  function suppressInvites() {
    persist(setInviteSuppressed(state.value))
  }

  function snoozeDays(days = 30) {
    persist(setSnoozed(state.value, Date.now() + days * 24 * 60 * 60 * 1000))
  }

  return {
    state,
    liked,
    suppressed,
    snoozed,
    likeIt,
    unlikeIt,
    takeAutoInvite,
    suppressInvites,
    snoozeDays,
  }
})
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/store/support.js frontend/tests/tip-support-contract.test.js
git commit -m "feat(tip): Pinia support store(薄封装纯函数层)"
```

---

## Task 4: 站级合规页脚(SiteFooter)+ Layout sticky 接线

先落 D1 的独立改造:把「数据仅供参考」的合规声明真正铺到全站页面底部,并在页脚右缘放一枚安静的「股东可顺手增资」入口(点开即打赏卡)。Task 5 的打赏卡在此之前还不在,因此本任务把 `TipSupportDialog` 的挂载与共享可见性一并建好,保证任务末**可独立打开一次打赏卡验收**(先用占位内容,Task 5 再补正式 UI)。

**Files:**
- Create: `frontend/src/components/support/useSupportUi.js`
- Create: `frontend/src/components/support/TipSupportDialog.vue`(本任务给**可编译骨架**,Task 5 落正式文案/布局)
- Create: `frontend/src/components/SiteFooter.vue`
- Modify: `frontend/src/components/Layout.vue`(import + `<SiteFooter />` + sticky-footer flex)
- Test: `frontend/tests/tip-support-contract.test.js`(Layout 断言已含于 Task 2,追加 footer 组件断言)

**Interfaces:**
- Consumes: Task 2 `SUPPORT_COPY`/`QR_IMAGES`。
- Produces:
  - `useSupportUi()` → `{ visible: Ref<boolean>, open(): void, close(): void }`(模块级单例,全站一份)。
  - `<SiteFooter />`(无 props/emits):自带打赏卡,任何页面底部常驻。
  - `<TipSupportDialog />`:props `visible: Boolean`,emits `update:visible`;Task 5 将扩展其内部,但挂载点(在 SiteFooter 内)不变。

- [ ] **Step 1: 追加 footer/Layout 契约断言(先失败)**

在 `frontend/tests/tip-support-contract.test.js` 末尾追加:

```js
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
  assert.match(footerSource, /不构成任何投资建议/)
  assert.match(footerSource, /useSupportUi/)
  assert.match(footerSource, /TipSupportDialog/)
  const counts = (re) => (footerSource.match(re) || []).length
  assert.equal(counts(/footerTipEntry/g), 1, '页脚只有一个静默入口')
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: FAIL —— `SiteFooter.vue` 不存在。

- [ ] **Step 3: 建共享可见性单例**

创建 `frontend/src/components/support/useSupportUi.js`:

```js
import { ref } from 'vue'

// 全站唯一的打赏卡可见性:顶栏 SupportButton 与页脚 SiteFooter 共用同一实例,
// 因此无论从哪个入口点开,都只会有一张打赏卡。
const visible = ref(false)

export function useSupportUi() {
  function open() { visible.value = true }
  function close() { visible.value = false }
  return { visible, open, close }
}
```

- [ ] **Step 4: 建打赏卡骨架(可编译、可点亮)**

创建 `frontend/src/components/support/TipSupportDialog.vue`:

```vue
<template>
  <el-dialog
    v-model="dialogVisible"
    class="tip-dialog"
    :title="null"
    :width="dialogWidth"
    align-center
    append-to-body
  >
    <div class="tip-dialog__body">
      <p class="tip-dialog__headline">股东增资卡(骨架先行,文案与码图随 Task 5 落地)</p>
      <p class="tip-dialog__sub">打赏支持 · 微信 / 支付宝个人收款码</p>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useSupportUi } from './useSupportUi'

defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['update:visible'])

const ui = useSupportUi()
const { isMobile } = useResponsive()
const dialogWidth = computed(() => (isMobile.value ? 'calc(100vw - 20px)' : '540px'))

const dialogVisible = computed({
  get: () => ui.visible.value,
  set: (value) => emit('update:visible', value),
})
</script>
```

- [ ] **Step 5: 实现 SiteFooter**

创建 `frontend/src/components/SiteFooter.vue`:

```vue
<template>
  <footer class="site-footer">
    <div class="site-footer__disclaimer">
      <span class="site-footer__name">{{ SUPPORT_COPY.footerSiteName }}</span>
      <span class="site-footer__muted">{{ SUPPORT_COPY.footerDisclaimer }}</span>
    </div>

    <button
      type="button"
      class="site-footer__tip"
      :aria-label="SUPPORT_COPY.footerTipAria"
      @click="ui.open()"
    >
      {{ SUPPORT_COPY.footerTipEntry }}
    </button>

    <TipSupportDialog v-model="ui.visible" />
  </footer>
</template>

<script setup>
import { SUPPORT_COPY } from './support/supportCopy'
import { useSupportUi } from './support/useSupportUi'
import TipSupportDialog from './support/TipSupportDialog.vue'

const ui = useSupportUi()
</script>

<style scoped>
.site-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-1) var(--spacing-4);
  flex: 0 0 auto;
  padding: var(--spacing-2) var(--spacing-4) var(--spacing-3);
  border-top: 1px solid var(--border-subtle);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  color: var(--text-tertiary);
}

.site-footer__disclaimer {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  min-width: 0;
}

.site-footer__name {
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.site-footer__tip {
  appearance: none;
  border: 0;
  background: transparent;
  padding: var(--spacing-1) 0;
  font: inherit;
  color: var(--text-tertiary);
  white-space: nowrap;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.site-footer__tip:hover {
  color: var(--text-link);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.site-footer__tip:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
  border-radius: var(--radius-xs);
}

@media (min-width: 768px) and (max-width: 1023px) {
  .site-footer {
    padding-inline: var(--spacing-3);
  }
}

@media (max-width: 767px) {
  .site-footer {
    padding-inline: var(--spacing-2);
  }
}
</style>
```

- [ ] **Step 6: 改 Layout 接线 + sticky-footer**

`frontend/src/components/Layout.vue`,模板 `<main>` 块后插页脚(`</main>` 与 `</div>` 之间):

```html
      </main>
      <SiteFooter />
```

`<script setup>` 的 import 区(在 `import GlobalSearch from './GlobalSearch.vue'` 之后)加:

```js
import SiteFooter from './SiteFooter.vue'
```

CSS:把 `.app-shell__main` 与 `.app-shell__content` 两段改成 flex 列 + `flex:1`,让短页面页脚也能贴底(内容区在短页本来就是页面底色,见 style.css `body{background:var(--surface-page)}`):

`.app-shell__main`(现状第 90-94 行)改为:

```css
.app-shell__main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 100dvh;
  margin-left: 168px;
}
```

`.app-shell__content`(现状第 96-99 行)改为:

```css
.app-shell__content {
  flex: 1 1 auto;
  min-height: 0;
  padding: 0 var(--spacing-4) var(--spacing-4);
}
```

同步改两块 media 里的 `.app-shell__content` 高度行:
- `@media (min-width:768px) and (max-width:1023px)` 内第 119-122 行 `min-height: calc(...)` → `min-height: 0;`(padding 保持 `0`)。
- `@media (max-width:767px)` 内第 135-138 行 `min-height: auto;` → `min-height: 0;`(padding 保持)。

- [ ] **Step 7: 跑测试 + build 门**

Run: `cd frontend && node --test tests/tip-support-contract.test.js tests/tip-support-state.test.js`
Expected: PASS。

Run: `cd frontend && npm run build`
Expected: build 成功,无 import/模板报错。

- [ ] **Step 8: 提交**

```bash
git add frontend/src/components/Layout.vue frontend/src/components/SiteFooter.vue frontend/src/components/support/useSupportUi.js frontend/src/components/support/TipSupportDialog.vue frontend/tests/tip-support-contract.test.js
git commit -m "feat(tip): 站级合规页脚 + 静默增资入口,Layout 接 sticky-footer"
```

---

## Task 5: 打赏卡正式化(双码占位 + 完整文案 + 隐身动作)

把 Task 4 的骨架换成正式股东情怀打赏卡:文案、双码区(占位卡/码图二选一)、掩码收款方、三条合规脚注、动作区(下次一定 / 暂时收起 30 天 / 继续看盘)。这里织入 Task 2 文案的合规与诚实边界。

**Files:**
- Modify: `frontend/src/components/support/TipSupportDialog.vue`
- Test: 契约测试已含合规词;本任务加 **build 门**(无组件级单测设施)。

**Interfaces:**
- Consumes: Task 2 `SUPPORT_COPY`、`QR_IMAGES`;Task 4 `useSupportUi`、`useResponsive`;Task 3 `useSupportStore.snoozeDays`(从组件内 import store 调用,无需改 store)。
- Produces:`<TipSupportDialog v-model>` 正式版;点击「暂时收起这个入口」会调用 `snoozeDays()` 并关闭。

- [ ] **Step 1: 重写 TipSupportDialog 模板/脚本**

整体替换 `frontend/src/components/support/TipSupportDialog.vue` 为:

```vue
<template>
  <el-dialog
    v-model="dialogVisible"
    class="tip-dialog"
    :title="null"
    :width="dialogWidth"
    align-center
    append-to-body
  >
    <div class="tip-dialog__body">
      <p class="tip-dialog__eyebrow">{{ SUPPORT_COPY.dialogEyebrow }}</p>
      <h3 class="tip-dialog__headline">{{ SUPPORT_COPY.dialogHead }}</h3>
      <p class="tip-dialog__sub">{{ SUPPORT_COPY.dialogSub }}</p>

      <p class="tip-dialog__amount">{{ SUPPORT_COPY.amountNote }}</p>
      <p class="tip-dialog__hint">{{ SUPPORT_COPY.scanHint }}</p>

      <div class="qr-grid">
        <figure v-for="side in qrSides" :key="side.key" class="qr-card">
          <figcaption class="qr-card__label">{{ side.label }}</figcaption>
          <img
            v-if="QR_IMAGES[side.key]"
            :src="QR_IMAGES[side.key]"
            :alt="`${side.label}收款二维码(析股台)`"
            class="qr-card__img"
          />
          <div v-else class="qr-card__placeholder" role="img" aria-label="收款码待作者上传">
            <span>{{ side.label }}收款码</span>
            <small>作者将码图放入 src/assets/support/<br />并在 qrImages.js 接线后显示</small>
          </div>
        </figure>
      </div>

      <p class="tip-dialog__trust">{{ SUPPORT_COPY.payeeMask }}</p>
      <p class="tip-dialog__collective">{{ SUPPORT_COPY.thanksCollective }}</p>

      <ol class="tip-dialog__compliance">
        <li>{{ SUPPORT_COPY.compliance1 }}</li>
        <li>{{ SUPPORT_COPY.compliance2 }}</li>
        <li>{{ SUPPORT_COPY.compliance3 }}</li>
      </ol>

      <p v-if="snoozedNotice" class="tip-dialog__snoozed" role="status">
        {{ SUPPORT_COPY.snoozedTip }}
      </p>
    </div>

    <template #footer>
      <el-button text @click="handleLater">{{ SUPPORT_COPY.actionLater }}</el-button>
      <el-button text @click="handleSnooze">{{ SUPPORT_COPY.snoozeAction }}</el-button>
      <el-button type="primary" @click="handleDone">{{ SUPPORT_COPY.actionPrimary }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useSupportStore } from '@/store/support'
import { QR_IMAGES } from './qrImages'
import { SUPPORT_COPY } from './supportCopy'
import { useSupportUi } from './useSupportUi'

defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['update:visible'])

const ui = useSupportUi()
const supportStore = useSupportStore()
const { isMobile } = useResponsive()
const snoozedNotice = ref(false)

const dialogWidth = computed(() => (isMobile.value ? 'calc(100vw - 20px)' : '540px'))
const dialogVisible = computed({
  get: () => ui.visible.value,
  set: (value) => emit('update:visible', value),
})

const qrSides = [
  { key: 'wechat', label: SUPPORT_COPY.qrWechatLabel },
  { key: 'alipay', label: SUPPORT_COPY.qrAlipayLabel },
]

function handleDone() { ui.close() }
function handleLater() { ui.close() }
function handleSnooze() {
  supportStore.snoozeDays(30)
  snoozedNotice.value = true
  window.setTimeout(() => {
    snoozedNotice.value = false
    ui.close()
  }, 1400)
}
</script>

<style scoped>
.tip-dialog__body {
  display: grid;
  gap: var(--spacing-3);
}

.tip-dialog__eyebrow {
  margin: 0;
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-support);
}

.tip-dialog__headline {
  margin: 0;
  font-size: var(--font-size-xl);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
}

.tip-dialog__sub,
.tip-dialog__amount,
.tip-dialog__hint,
.tip-dialog__collective,
.tip-dialog__trust,
.tip-dialog__snoozed {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: var(--line-height-relaxed);
}

.tip-dialog__amount {
  color: var(--text-primary);
  font-weight: 500;
}

.tip-dialog__trust {
  font-size: var(--font-size-xs);
  color: var(--text-warning);
}

.tip-dialog__hint { font-size: var(--font-size-xs); }

.qr-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.qr-card {
  margin: 0;
  display: grid;
  justify-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-canvas);
}

.qr-card__label { font-size: var(--font-size-sm); color: var(--text-primary); font-weight: 500; }

.qr-card__img {
  width: 168px;
  height: 168px;
  object-fit: contain;
}

.qr-card__placeholder {
  width: 168px;
  height: 168px;
  display: grid;
  place-content: center;
  gap: var(--spacing-2);
  text-align: center;
  border-radius: var(--radius-sm);
  background: var(--surface-panel-muted);
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.qr-card__placeholder small {
  display: block;
  line-height: var(--line-height-normal);
  white-space: pre-line;
}

.tip-dialog__compliance {
  margin: 0;
  padding-left: var(--spacing-4);
  display: grid;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  color: var(--text-tertiary);
}

.tip-dialog__snoozed { color: var(--color-support); }

@media (max-width: 420px) {
  .qr-grid { grid-template-columns: 1fr; }
  .qr-card__img,
  .qr-card__placeholder { width: 152px; height: 152px; }
}
</style>
```

- [ ] **Step 2: build + 全量 node --test**

Run: `cd frontend && npm run build`
Expected: 成功。

Run: `cd frontend && node --test tests/tip-support-state.test.js tests/tip-support-contract.test.js`
Expected: PASS(合规词断言锁死本卡文案)。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/support/TipSupportDialog.vue
git commit -m "feat(tip): 打赏卡正式化(双码占位/合规脚注/30 天隐身动作)"
```

---

## Task 6: 顶栏「点赞为股」入口 + 自绘确认卡

方向三的入口本体:内联 SVG 拇指(点亮变金),点按驱动 确认卡 → 顺带增资 → 打赏卡 的两段式动线;吸收方向二的「点开降级 + 30 天隐身」;吸收「确认卡里支持撤回 / 永久关增资 / 收起入口」;点亮态只用 `--color-support-*` 别名,不改 EP 琥珀默认。

**Files:**
- Create: `frontend/src/components/app/SupportButton.vue`
- Test: 契约测试追加(断言 CommandBar 接线 + SupportButton 关键结构,见 Task 7 一起;本任务自证靠 **build 门 + dev 冒烟说明**)。

**Interfaces:**
- Consumes: Task 1 闸门语义(经 store)、Task 3 `useSupportStore`、Task 4 `useSupportUi`、Task 2 `SUPPORT_COPY`。
- Produces:`<SupportButton />`(无 props/emits),挂载点由 Task 7 决定。

**行为规约(实现必须满足):**
1. `store.snoozed` 为 true → 不渲染(30 天隐身)。
2. 按钮语义:未点亮=描边拇指;点亮=金色实心拇指。文案随屏宽:桌面(≥1024)显示「点赞/已一票」小字,<1024 只图标。`aria-pressed` 同步点亮态。
3. 点击未点亮:调 `likeIt()`;再调 `takeAutoInvite()`——返回 true 才在确认卡里展示**大号**「顺带增资?」(这是唯一的自动邀赏窗口,每天 ≤1 次、终身 ≤3 次、可永久关);无论是否拿到大号,都弹出确认卡。
4. 点击已点亮(手动):也弹出确认卡;`takeAutoInvite()` 未放行(配额耗尽/已永久关)或手动进卡时,只给**小号**「顺带增资 →」幽灵链(不消耗自动配额)。
5. 确认卡按钮:
   - 大号邀请:[顺带增资?](主)打开打赏卡并收卡;[先不了,白嫖也是股东权益。](幽灵)只收卡。
   - 小号入口:一行幽灵链,同样打开打赏卡。
   - 底部小字行:[收回这一票]·[以后别再提增资]·[暂时收起这个入口]。撤回=熄灯并收卡(无行内反馈);「以后别再提增资」后大小号入口都不再出现(打赏仍可从页脚入口进入);「收起」=`snoozeDays(30)` 收卡。
6. 浮层为**自绘绝对定位**(顶栏右缘),点外部/Esc 关闭;移动端宽度 `min(340px, 100vw - 16px)`;层级用 `--z-dropdown`。

- [ ] **Step 1: 实现 SupportButton(唯一权威稿)**

创建 `frontend/src/components/app/SupportButton.vue`,完整内容如下(模板 + 脚本 + 样式齐全,无第二稿):

```vue
<template>
  <div v-if="!supportStore.snoozed" class="support-entry">
    <button
      type="button"
      class="support-btn"
      :class="{ 'support-btn--liked': supportStore.liked }"
      :aria-pressed="supportStore.liked"
      :title="supportStore.liked ? SUPPORT_COPY.entryTitleLiked : SUPPORT_COPY.entryTitleIdle"
      @click="handleToggle"
    >
      <svg
        class="support-btn__thumb"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z" />
        <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
      </svg>
      <span v-if="isDesktop" class="support-btn__label">
        {{ supportStore.liked ? SUPPORT_COPY.labelLiked : SUPPORT_COPY.labelIdle }}
      </span>
    </button>

    <button
      v-if="panelOpen"
      type="button"
      class="support-confirm__scrim"
      tabindex="-1"
      aria-hidden="true"
      @click="closePanel"
    ></button>

    <div v-if="panelOpen" class="support-confirm" role="dialog" aria-label="点赞确认卡">
      <p class="support-confirm__head">{{ SUPPORT_COPY.confirmHead }}</p>
      <p class="support-confirm__sub">{{ SUPPORT_COPY.confirmSub }}</p>
      <p class="support-confirm__note">{{ SUPPORT_COPY.confirmLocalNote }}</p>

      <template v-if="bigInvite">
        <p class="support-confirm__invite-text">{{ SUPPORT_COPY.inviteLead }}</p>
        <div class="support-confirm__actions">
          <el-button type="primary" size="small" @click="openTip">
            {{ SUPPORT_COPY.inviteAction }}
          </el-button>
          <el-button text size="small" @click="closePanel">
            {{ SUPPORT_COPY.inviteDecline }}
          </el-button>
        </div>
      </template>
      <button v-else-if="showGhostInvite" type="button" class="support-confirm__ghost" @click="openTip">
        {{ SUPPORT_COPY.inviteGhost }}
      </button>

      <div class="support-confirm__links">
        <button v-if="supportStore.liked" type="button" @click="revoke">
          {{ SUPPORT_COPY.revokeAction }}
        </button>
        <button v-if="!supportStore.suppressed" type="button" @click="suppress">
          {{ SUPPORT_COPY.suppressAction }}
        </button>
        <button type="button" @click="snooze">
          {{ SUPPORT_COPY.snoozeAction }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useSupportStore } from '@/store/support'
import { SUPPORT_COPY } from '../support/supportCopy'
import { useSupportUi } from '../support/useSupportUi'

const supportStore = useSupportStore()
const ui = useSupportUi()
const { isDesktop } = useResponsive()

const panelOpen = ref(false)
const bigInvite = ref(false)        // 刚点亮且拿到自动配额 → 大号「顺带增资?」
const showGhostInvite = ref(false)  // 手动进卡 / 配额耗尽 → 小号幽灵入口

function onKeydown(e) {
  if (e.key === 'Escape') closePanel()
}
function removeKeydown() {
  window.removeEventListener('keydown', onKeydown)
}
function closePanel() {
  panelOpen.value = false
  bigInvite.value = false
  showGhostInvite.value = false
  removeKeydown()
}
async function openPanel() {
  panelOpen.value = true
  await nextTick()
  window.addEventListener('keydown', onKeydown)
}

function handleToggle() {
  if (panelOpen.value) {
    closePanel()
    return
  }
  if (supportStore.liked) {
    // 手动点开已点亮:只给幽灵小入口,不消耗自动配额
    bigInvite.value = false
    showGhostInvite.value = !supportStore.suppressed
    openPanel()
    return
  }
  const becameLiked = supportStore.likeIt()
  if (!becameLiked) return
  bigInvite.value = supportStore.takeAutoInvite()
  showGhostInvite.value = !bigInvite.value && !supportStore.suppressed
  openPanel()
}

function revoke() {
  supportStore.unlikeIt()
  closePanel()
}
function suppress() {
  supportStore.suppressInvites()
  closePanel()
}
function snooze() {
  supportStore.snoozeDays(30)
  closePanel()
}
function openTip() {
  closePanel()
  ui.open()
}

onBeforeUnmount(removeKeydown)
</script>

<style scoped>
.support-entry {
  position: relative;
  display: inline-flex;
}

.support-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  height: 44px;
  padding: 0 var(--spacing-1);
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition:
    background var(--transition-fast),
    color var(--transition-fast);
}

.support-btn:hover {
  background: var(--surface-panel-muted);
}

.support-btn--liked {
  color: var(--color-support);
}

.support-btn--liked .support-btn__thumb {
  fill: currentColor;
}

.support-btn__thumb {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
}

.support-btn__label {
  font-size: var(--font-size-xs);
  line-height: 1;
  color: inherit;
  white-space: nowrap;
}

.support-btn:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 1px;
  border-radius: var(--radius-md);
}

.support-confirm {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: var(--z-dropdown);
  box-sizing: border-box;
  width: min(340px, calc(100vw - 16px));
  display: grid;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-overlay);
  text-align: left;
}

.support-confirm__scrim {
  position: fixed;
  inset: 0;
  z-index: calc(var(--z-dropdown) - 1);
  background: transparent;
  border: 0;
  cursor: default;
}

.support-confirm__head {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 600;
  line-height: var(--line-height-tight);
  color: var(--text-primary);
}

.support-confirm__sub {
  margin: 0;
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
}

.support-confirm__note {
  margin: 0;
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  color: var(--text-tertiary);
}

.support-confirm__invite-text {
  margin: var(--spacing-1) 0 0;
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-subtle);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
}

.support-confirm__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.support-confirm__ghost {
  margin-top: var(--spacing-1);
  padding: var(--spacing-1) 0;
  appearance: none;
  border: 0;
  background: none;
  font: inherit;
  font-size: var(--font-size-sm);
  color: var(--text-link);
  cursor: pointer;
  text-align: left;
}

.support-confirm__ghost:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.support-confirm__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1) var(--spacing-4);
  margin-top: var(--spacing-1);
  padding-top: var(--spacing-2);
  border-top: 1px dashed var(--border-subtle);
}

.support-confirm__links button {
  padding: 0;
  appearance: none;
  border: 0;
  background: none;
  font: inherit;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  cursor: pointer;
}

.support-confirm__links button:hover {
  color: var(--text-link);
}

.support-confirm__ghost:focus-visible,
.support-confirm__links button:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
  border-radius: var(--radius-xs);
}
</style>
```

行为对照(实现完成即满足;契约测试不覆盖视觉,靠冒烟清单收口):
- `snoozed` → 整块不渲染(30 天隐身);「暂时收起这个入口」在确认卡里 = `snoozeDays(30)`。
- 未点亮:描边拇指;点亮:金色实心(`--color-support`,别名映射品牌金,不改 EP 琥珀)。
- 桌面(≥1024)图标旁有小字「点赞 / 已一票」,<1024 只有图标(`isDesktop` 由 useResponsive 提供)。
- 大号 CTA 仅在「刚点亮且 `takeAutoInvite()` 放行」时出现;手动再点亮给幽灵小入口;「以后别再提增资」后两者都消失,只在用户主动再点亮时连幽灵入口也不给(用户明确拒绝过)。
- 点外部(scrim)/Esc/「先不了」收卡;「收回这一票」熄灯收卡;「继续看盘」路径 = 打赏卡关闭按钮。

- [ ] **Step 2: build + 全量 node --test**

Run: `cd frontend && npm run build`
Expected: 成功(无未使用 import / 模板报错)。

Run: `cd frontend && node --test tests/tip-support-state.test.js tests/tip-support-contract.test.js`
Expected: PASS。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/app/SupportButton.vue
git commit -m "feat(tip): 顶栏点赞为股入口 + 自绘确认卡(大/小邀赏 · 撤回/关增资/收起 30 天)"
```

## Task 7: CommandBar 接线 + 终验(全量测试/build/冒烟要点)

把顶栏入口接进右簇,并做收尾验证与说明。

**Files:**
- Modify: `frontend/src/components/app/CommandBar.vue`(模板 :23-24 之间插 `<SupportButton />`;脚本 import)
- Test: `frontend/tests/tip-support-contract.test.js` 追加接线断言
- 收尾:全量 `node --test tests/*.test.js` + `npm run build` + 手工冒烟要点记录

**Interfaces:**
- Consumes: Task 6 `<SupportButton />`。
- Produces: 全站顶栏常驻入口。

- [ ] **Step 1: 追加接线契约(先失败)**

在 `frontend/tests/tip-support-contract.test.js` 末尾追加:

```js
const commandBarSource = await readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8')

test('CommandBar 右簇接入 SupportButton', () => {
  assert.match(commandBarSource, /import\s+SupportButton\s+from\s+['"].*SupportButton\.vue['"]/)
  assert.match(commandBarSource, /<SupportButton\s*\/?>/)
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: FAIL —— CommandBar 尚无 SupportButton。

- [ ] **Step 3: 接线**

模板 `.command-bar__right`(`frontend/src/components/app/CommandBar.vue:22-25`)改为:

```html
    <div class="command-bar__right">
      <NotificationBell />
      <SupportButton />
      <CommandBarUtilities />
    </div>
```

脚本 import(在 `import CommandBarUtilities from './CommandBarUtilities.vue'` 之后)加:

```js
import SupportButton from './SupportButton.vue'
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd frontend && node --test tests/tip-support-contract.test.js`
Expected: PASS。

- [ ] **Step 5: 全量回归**

Run: `cd frontend && node --test tests/*.test.js`
Expected: 全绿(仓库现有契约 + 本功能 2 份)。

Run: `cd frontend && npm run build`
Expected: 成功。

- [ ] **Step 6: 手工冒烟要点(记录到提交说明,非自动化)**

如可起 `npm run dev`(5173)逐条过:
1. 任意页底部有页脚;点「股东可顺手增资 ↗」→ 打赏卡出现(双占位卡 + 合规脚注 3 条)。
2. 顶栏点亮:图标变金、出现确认卡、大号「顺带增资?」;点「先不了」收卡,点亮态保留。
3. 再点已点亮图标 → 确认卡只给幽灵「顺带增资 →」。
4. 确认卡「收回这一票」→ 熄灯;「以后别再提增资」后不再出大号;「暂时收起这个入口」→ 入口消失 30 天(刷新仍在,因存 localStorage)。
5. 打赏卡「下次一定 / 继续看盘」均关闭;「暂时收起这个入口」→ 倒计时提示后关闭且顶栏入口消失。
6. 移动端(≤767):顶栏只剩图标(无「点赞」小字),浮层宽度不超屏;页脚入口可点。

- [ ] **Step 7: 提交**

```bash
git add frontend/src/components/app/CommandBar.vue frontend/tests/tip-support-contract.test.js
git commit -m "feat(tip): CommandBar 右簇接入点赞为股入口;契约断言收口"
```

---

## Self-Review(计划自检,非子代理)

**Spec 覆盖核对:**
- D3 两段式(点赞点亮 → 确认卡 → 顺带增资 → 打赏卡):Task 6 大/小邀赏 + Task 5 打赏卡。✓
- D2 状态机吸收(pill→icon→30 天隐身):Task 6(桌面文字点亮后变「已一票」的降级语义 + snoozeDays 30 天,store/纯函数承接)。✓
- D1 先落站级合规页脚 + 静默入口:Task 4。✓
- 5 条必改点:金撞色(#1)→ Task 2 tokens 别名 + Task 6 拇指形状;「后台看到每笔」→ supportCopy 只留集体致谢(契约锁);移动双码叠放 + 点亮后再点回确认卡 → Task 5 单列(≤420 竖排)+ Task 6 手动进卡;金额随缘小额引导 → `amountNote`。✓
- 红线词/未成年/澄清/无计数/不伪造到账:契约测试 FORBIDDEN + mustHave 锁死。✓

**占位符扫描:** 全文无 TBD/TODO;Task 5 的占位卡是**刻意产品状态**(作者后贴码),不是计划占位。

**类型一致性:** `likeIt()/takeAutoInvite()/snoozeDays(30)/suppressed/snoozed/liked` 等名字在 Task 1(纯函数)、Task 3(store)、Task 6(调用)三处一致;`SUPPORT_COPY` 字段名在 Task 2 定义、Task 4/5/6 引用处一致;`QR_IMAGES` key `wechat/alipay` 全链一致;`--color-support-50/500` 定义与断言一致。✓

**已知有意保留项:** 无组件级单测设施(仓库无 vitest),UI 行为以契约测试(源码文本)+ build + 冒烟清单覆盖;store 因 import `vue/pinia` 且 node 下 ESM 互操作不稳,采用源码契约而非真调用——纯逻辑已由 Task 1 真单测覆盖,store 只是转发。
