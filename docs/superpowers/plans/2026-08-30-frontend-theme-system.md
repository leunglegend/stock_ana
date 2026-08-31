# Frontend Theme System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为股票研究工作台增加默认 Ocean 主题及 Jade、Charcoal 两套可持久化皮肤，并从顶部命令栏实时切换。

**Architecture:** 使用根元素 `data-theme` 驱动 CSS 语义 Token 覆盖；纯 JavaScript 主题模块负责白名单校验、持久化、DOM 应用与变更事件。Vue 命令栏只负责呈现主题菜单，K 线组件监听主题事件并重新计算 ECharts option。

**Tech Stack:** Vue 3、Element Plus、CSS Custom Properties、ECharts、Node.js `node:test`、Vite

---

## File Map

- Create `frontend/src/theme.js`: 主题元数据、校验、读取、应用、持久化及事件契约。
- Create `frontend/tests/theme.test.js`: 使用伪 DOM 与伪存储验证主题模块行为。
- Modify `frontend/src/main.js`: Vue 挂载前恢复主题，避免首屏颜色闪烁。
- Modify `frontend/src/styles/tokens.css`: Ocean 默认 Token 及 Jade、Charcoal 覆盖。
- Modify `frontend/src/components/app/CommandBar.vue`: 顶部主题按钮、菜单、预览色与移动端适配。
- Modify `frontend/src/components/app/DesktopSidebar.vue`: 使用主题侧栏语义 Token，形成更明确的工作台层级。
- Modify `frontend/src/components/KLineChart.vue`: 监听主题事件并触发 chart option 重算。

### Task 1: Theme state contract

**Files:**
- Create: `frontend/src/theme.js`
- Create: `frontend/tests/theme.test.js`

- [ ] **Step 1: Write failing theme tests**

测试覆盖默认回退、合法存储恢复、非法值回退、DOM 属性更新、持久化失败降级和 `app-theme-change` 事件。核心断言：

```js
assert.equal(resolveTheme('jade'), 'jade')
assert.equal(resolveTheme('unknown'), DEFAULT_THEME)
assert.equal(loadTheme(storageWith('charcoal')), 'charcoal')
assert.equal(applyTheme('jade', { root, storage }), 'jade')
assert.equal(root.dataset.theme, 'jade')
assert.equal(dispatched.type, THEME_CHANGE_EVENT)
```

- [ ] **Step 2: Run tests and confirm the missing-module failure**

Run: `cd frontend && node --test tests/theme.test.js`

Expected: FAIL because `src/theme.js` does not exist.

- [ ] **Step 3: Implement the minimal theme module**

Public contract:

```js
export const DEFAULT_THEME = 'ocean'
export const THEME_CHANGE_EVENT = 'app-theme-change'
export const THEME_STORAGE_KEY = 'stock-analyzer-theme'
export const THEMES = Object.freeze([
  { key: 'ocean', name: '深海蓝 × 金色', colors: ['#172a3d', '#d9a441', '#f4f6f8'] },
  { key: 'jade', name: '墨绿 × 琥珀', colors: ['#133f3a', '#e7a43b', '#edf4f1'] },
  { key: 'charcoal', name: '炭黑 × 朱砂', colors: ['#262b33', '#b8583e', '#f5f3ef'] },
])

const themeKeys = new Set(THEMES.map(({ key }) => key))

export function resolveTheme(value) {
  return themeKeys.has(value) ? value : DEFAULT_THEME
}

export function loadTheme(storage = globalThis.localStorage) {
  try { return resolveTheme(storage?.getItem(THEME_STORAGE_KEY)) }
  catch { return DEFAULT_THEME }
}

export function applyTheme(theme, { root = globalThis.document?.documentElement, storage = globalThis.localStorage, dispatch = globalThis.dispatchEvent } = {}) {
  const resolved = resolveTheme(theme)
  if (root) root.dataset.theme = resolved
  try { storage?.setItem(THEME_STORAGE_KEY, resolved) } catch {}
  dispatch?.(new CustomEvent(THEME_CHANGE_EVENT, { detail: { theme: resolved } }))
  return resolved
}

export function initializeTheme(options = {}) {
  return applyTheme(loadTheme(options.storage), options)
}
```

所有浏览器全局对象都通过参数或存在性检查访问，保证 Node 测试可运行。存储异常只影响持久化，不影响当前 DOM 主题。

- [ ] **Step 4: Run focused tests**

Run: `cd frontend && node --test tests/theme.test.js`

Expected: all theme tests PASS.

### Task 2: Theme tokens and startup restoration

**Files:**
- Modify: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/main.js`
- Modify: `frontend/tests/theme.test.js`

- [ ] **Step 1: Add source-contract assertions**

读取 `tokens.css` 和 `main.js`，断言存在三个主题选择器、主题侧栏变量，并且 `initializeTheme()` 出现在 `createApp(App)` 之前。

```js
assert.match(tokensSource, /\[data-theme=['"]jade['"]\]/)
assert.match(tokensSource, /\[data-theme=['"]charcoal['"]\]/)
assert.match(tokensSource, /--surface-sidebar:/)
assert.ok(mainSource.indexOf('initializeTheme()') < mainSource.indexOf('createApp(App)'))
```

- [ ] **Step 2: Run tests and verify contract failure**

Run: `cd frontend && node --test tests/theme.test.js`

Expected: FAIL because selectors, semantic sidebar variables and startup initialization are absent.

- [ ] **Step 3: Define complete theme overrides**

保留上涨、下跌、错误和警告 Token 不变。为三套主题定义或覆盖：

```css
--color-primary-50 ... --color-primary-900;
--color-accent-50; --color-accent-500; --color-accent-700;
--surface-page; --surface-canvas; --surface-panel;
--surface-panel-muted; --surface-panel-strong;
--surface-sidebar; --surface-sidebar-hover; --surface-sidebar-active;
--text-sidebar; --text-sidebar-muted;
--border-default; --border-strong; --focus-ring; --focus-ring-soft;
--surface-ai; --text-ai; --border-ai;
--chart-grid; --chart-axis; --chart-ma5; --chart-ma10; --chart-ma20;
--chart-dif; --chart-dea; --chart-k; --chart-d; --chart-j;
```

Ocean 放在 `:root`，Jade 与 Charcoal 使用 `:root[data-theme='...']` 覆盖。所有正文/背景组合满足 WCAG AA。

- [ ] **Step 4: Restore theme before Vue mount**

在 `main.js` 导入并调用：

```js
import { initializeTheme } from './theme'

initializeTheme()
const app = createApp(App)
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && node --test tests/theme.test.js tests/bundle-entry.test.js`

Expected: all tests PASS.

### Task 3: Theme picker and shell color hierarchy

**Files:**
- Modify: `frontend/src/components/app/CommandBar.vue`
- Modify: `frontend/src/components/app/DesktopSidebar.vue`

- [ ] **Step 1: Add source-contract tests for the picker**

断言命令栏导入 `THEMES`、`applyTheme`、调色盘图标，存在可访问名称、当前主题标记和色板 swatch；断言侧栏消费 `--surface-sidebar`。

- [ ] **Step 2: Run tests and confirm they fail**

Run: `cd frontend && node --test tests/theme.test.js`

Expected: FAIL because the picker and sidebar theme variables are absent.

- [ ] **Step 3: Implement the command-bar picker**

用 `el-dropdown` 和 Element Plus `Brush` 图标增加独立按钮。状态初始化自根元素：

```js
const currentTheme = ref(document.documentElement.dataset.theme || DEFAULT_THEME)
function selectTheme(theme) {
  currentTheme.value = applyTheme(theme)
}
```

每个菜单项显示三个色块、中文主题名和当前项 `Check` 图标。按钮使用 `aria-label="切换界面主题"`、tooltip 及 `44x44px` 固定尺寸。

- [ ] **Step 4: Apply sidebar semantic colors**

侧栏背景改为 `--surface-sidebar`，品牌、导航文字、hover 和 active 状态分别消费 sidebar Token；Logo 使用强调色。嵌入抽屉时仍保持完整宽度与可读对比度。

- [ ] **Step 5: Run tests and build**

Run: `cd frontend && node --test tests/theme.test.js tests/bundle-entry.test.js && npm run build`

Expected: tests PASS and Vite build exits 0.

### Task 4: Runtime chart refresh

**Files:**
- Modify: `frontend/src/components/KLineChart.vue`
- Modify: `frontend/tests/theme.test.js`

- [ ] **Step 1: Add source-contract test**

断言 K 线组件监听并清理 `THEME_CHANGE_EVENT`，且 chart option 依赖响应式主题版本号。

- [ ] **Step 2: Run test and verify failure**

Run: `cd frontend && node --test tests/theme.test.js`

Expected: FAIL because the event listener is absent.

- [ ] **Step 3: Add lifecycle-safe chart invalidation**

```js
const themeVersion = ref(0)
function refreshTheme() { themeVersion.value += 1 }
onMounted(() => window.addEventListener(THEME_CHANGE_EVENT, refreshTheme))
onUnmounted(() => window.removeEventListener(THEME_CHANGE_EVENT, refreshTheme))

const chartOption = computed(() => {
  themeVersion.value
  // existing option construction
})
```

- [ ] **Step 4: Run focused and regression tests**

Run: `cd frontend && node --test tests/theme.test.js tests/bundle-entry.test.js`

Expected: all tests PASS.

### Task 5: Integrated visual verification

**Files:**
- Modify only if verification exposes a scoped theme defect.

- [ ] **Step 1: Run completion commands**

Run: `cd frontend && node --test tests/*.test.js && npm run build`

Expected: all tests PASS and build exits 0.

- [ ] **Step 2: Start the frontend without replacing existing processes**

Run: `cd frontend && npm run dev -- --host 0.0.0.0`

Expected: Vite prints an available local URL; if `5173` is occupied, use the next free port.

- [ ] **Step 3: Verify desktop and mobile theme behavior**

Using browser automation, inspect representative dashboard views at `360x800`, `390x844`, `768x1024` and `1440x900` for all three themes. Confirm:

- command-bar picker is visible and operable;
- theme changes page, sidebar, panels and controls without reload;
- refresh restores the selected theme;
- no horizontal overflow, overlap or clipped labels;
- red/green market semantics remain unchanged;
- screenshots are nonblank and show distinct themes.

- [ ] **Step 4: Run contrast checks**

Check computed foreground/background pairs for body, sidebar navigation, links, buttons and AI panels. Required contrast: normal text at least `4.5:1`, large text and UI boundaries at least `3:1`.

- [ ] **Step 5: Review diff boundaries**

Run: `git diff --check && git status --short && git diff -- frontend/src/theme.js frontend/tests/theme.test.js frontend/src/main.js frontend/src/styles/tokens.css frontend/src/components/app/CommandBar.vue frontend/src/components/app/DesktopSidebar.vue frontend/src/components/KLineChart.vue`

Expected: no whitespace errors; only task-related changes are attributed to this implementation. Existing unrelated user changes remain intact.

## Git Gate

The repository rules require confirmation before Git history changes. Do not execute the commit steps automatically. After verification, present the scoped file list and a suggested commit message such as `feat(frontend): 增加多主题换肤功能`, then wait for explicit approval before committing.
