# Opportunity Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增以板块涨幅为入口的“机会雷达”一级菜单，让用户在双栏工作台内发现领先板块、下钻成分股并进入详情或加入自选。

**Architecture:** 页面由 `OpportunityRadar.vue` 编排，展示组件只接收 props 和发出事件；`useOpportunityRadar.js` 负责 API 请求、60 秒缓存、选择状态和请求竞态；`opportunityRadar.js` 保存可直接用 Node 测试的排序、过滤、分页、缺失值和缓存工具。完全复用现有板块 API、用户 Store 与自选 Store，不修改后端、数据库或依赖。

**Tech Stack:** Vue 3 Composition API、Pinia、Vue Router、Element Plus、Node.js test runner、Vite、Playwright 临时 CLI

**Delivery Guard:** 计划中的 commit 步骤只有在用户明确授权 Git 提交后执行；未授权时只保留工作区改动并继续验证。

---

## File Map

**Create**

- `frontend/src/utils/opportunityRadar.js`：纯排序、过滤、分页、缺失值与定时缓存工具
- `frontend/src/composables/useOpportunityRadar.js`：榜单/成分股请求、状态、缓存和请求失效
- `frontend/src/components/radar/RadarToolbar.vue`：类型切换、搜索、仅上涨、刷新
- `frontend/src/components/radar/BoardRanking.vue`：板块涨幅榜和选择状态
- `frontend/src/components/radar/BoardSnapshot.vue`：当前板块摘要
- `frontend/src/components/radar/BoardStockTable.vue`：成分股分页和行操作
- `frontend/src/views/OpportunityRadar.vue`：页面编排、路由和加入自选流程
- `frontend/tests/opportunity-radar.test.js`：纯数据规则、缓存和请求 gate 单元测试
- `frontend/tests/opportunity-radar-contract.test.js`：路由、导航、组件边界和可访问性契约测试

**Modify**

- `frontend/src/router/index.js`：注册 `/radar` 懒加载路由
- `frontend/src/components/Layout.vue`：加入“雷达”一级菜单
- `frontend/src/components/app/MobileNav.vue`：导航列数由菜单数量驱动
- `frontend/tests/layout-contract.test.js`：把 `OpportunityRadar` 纳入统一工作台契约

## Task 1: Pure Radar Data Rules

**Files:**

- Create: `frontend/tests/opportunity-radar.test.js`
- Create: `frontend/src/utils/opportunityRadar.js`

- [ ] **Step 1: Write failing tests for board filtering, sorting, missing values and paging**

```js
import assert from 'node:assert/strict'
import test from 'node:test'
import {
  filterAndSortBoards,
  normalizeOptionalMetric,
  paginateRows,
} from '../src/utils/opportunityRadar.js'

test('板块按涨跌幅降序并支持名称和仅上涨过滤', () => {
  const boards = [
    { name: '银行', change_pct: 1.2 },
    { name: '半导体', change_pct: 3.8 },
    { name: '白酒', change_pct: -0.4 },
    { name: '零值', change_pct: 0 },
  ]
  assert.deepEqual(
    filterAndSortBoards(boards, { keyword: '', onlyRising: true }).map(({ name }) => name),
    ['半导体', '银行'],
  )
  assert.deepEqual(
    filterAndSortBoards(boards, { keyword: '银', onlyRising: false }).map(({ name }) => name),
    ['银行'],
  )
})

test('缺失指标与真实零值保持可区分', () => {
  assert.equal(normalizeOptionalMetric(undefined), null)
  assert.equal(normalizeOptionalMetric(Number.NaN), null)
  assert.equal(normalizeOptionalMetric(0), 0)
})

test('成分股分页不修改输入数组', () => {
  const rows = Array.from({ length: 25 }, (_, index) => ({ code: String(index) }))
  assert.deepEqual(paginateRows(rows, 2, 20), rows.slice(20))
  assert.equal(rows.length, 25)
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend && node --test tests/opportunity-radar.test.js`

Expected: FAIL because `src/utils/opportunityRadar.js` does not exist.

- [ ] **Step 3: Implement the minimum pure functions**

```js
export function normalizeOptionalMetric(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

export function filterAndSortBoards(boards = [], options = {}) {
  const query = String(options.keyword || '').trim().toLowerCase()
  return boards
    .filter((board) => !query || String(board.name || '').toLowerCase().includes(query))
    .filter((board) => !options.onlyRising || normalizeOptionalMetric(board.change_pct) > 0)
    .slice()
    .sort((left, right) => (normalizeOptionalMetric(right.change_pct) ?? -Infinity)
      - (normalizeOptionalMetric(left.change_pct) ?? -Infinity))
}

export function sortBoardStocks(stocks = []) {
  return stocks.slice().sort((left, right) => (normalizeOptionalMetric(right.change_pct) ?? -Infinity)
    - (normalizeOptionalMetric(left.change_pct) ?? -Infinity))
}

export function paginateRows(rows, page, pageSize) {
  const start = (page - 1) * pageSize
  return rows.slice(start, start + pageSize)
}
```

- [ ] **Step 4: Add tests and implementation for timed cache and request gate**

```js
test('定时缓存命中后会在 60 秒过期', () => {
  let now = 1000
  const cache = createTimedCache(60_000, () => now)
  cache.set('industry', ['cached'])
  assert.deepEqual(cache.get('industry'), ['cached'])
  now = 61_001
  assert.equal(cache.get('industry'), undefined)
})

test('请求 gate 只接受最后一次请求', () => {
  const gate = createRequestGate()
  const first = gate.next('stocks')
  const second = gate.next('stocks')
  assert.equal(gate.isCurrent('stocks', first), false)
  assert.equal(gate.isCurrent('stocks', second), true)
})
```

Implement `createTimedCache(ttlMs, now)` with `get/set/delete/clear`, and `createRequestGate()` with per-channel counters and `next/isCurrent/invalidate`.

- [ ] **Step 5: Run the focused test and verify GREEN**

Run: `cd frontend && node --test tests/opportunity-radar.test.js`

Expected: all radar utility tests PASS.

- [ ] **Step 6: Commit checkpoint when authorized**

```bash
git add frontend/src/utils/opportunityRadar.js frontend/tests/opportunity-radar.test.js
git commit -m "feat(radar): 增加雷达数据规则"
```

## Task 2: Radar State and API Orchestration

**Files:**

- Create: `frontend/src/composables/useOpportunityRadar.js`
- Modify: `frontend/tests/opportunity-radar.test.js`

- [ ] **Step 1: Add source-contract tests for API ownership and race protection**

```js
const composableSource = await readFile(
  new URL('../src/composables/useOpportunityRadar.js', import.meta.url),
  'utf8',
)

test('雷达组合式函数集中持有三个现有板块 API 与请求 gate', () => {
  assert.match(composableSource, /getBoardIndustry/)
  assert.match(composableSource, /getBoardConcept/)
  assert.match(composableSource, /getBoardStocks/)
  assert.match(composableSource, /createRequestGate/)
  assert.match(composableSource, /createTimedCache/)
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend && node --test tests/opportunity-radar.test.js`

Expected: FAIL because `useOpportunityRadar.js` does not exist.

- [ ] **Step 3: Implement state, derived data and public actions**

`useOpportunityRadar` must expose this stable interface:

```js
return {
  activeType, keyword, onlyRising, selectedBoard, boardPage, stockPage,
  activeBoards, filteredBoards, paginatedStocks,
  boardsLoading, boardsRefreshing, boardsError,
  stocksLoading, stocksRefreshing, stocksError,
  lastUpdatedAt,
  selectType, selectBoard, refresh, retryBoards, retryStocks,
}
```

Implementation requirements:

- Keep independent `industry` and `concept` records: `{ data, loading, refreshing, error, selectedName, updatedAt }`.
- On mount, request both lists using `Promise.allSettled`; do not let one rejection reject the other.
- Cache list results under `boards:industry` and `boards:concept` for 60 seconds.
- Cache stock results under `stocks:${type}:${board.name}` for 60 seconds.
- Auto-select the first filtered board when the current selection becomes unavailable.
- Use request gate channels `boards:${type}` and `stocks`; check the token before every visible state write.
- During manual refresh, retain old data, set `refreshing`, and update `updatedAt` only after success.
- Reset stock page to 1 whenever the selected board changes.

- [ ] **Step 4: Run focused tests and build**

Run: `cd frontend && node --test tests/opportunity-radar.test.js && npm run build`

Expected: radar tests PASS and Vite build exits 0.

- [ ] **Step 5: Commit checkpoint when authorized**

```bash
git add frontend/src/composables/useOpportunityRadar.js frontend/tests/opportunity-radar.test.js
git commit -m "feat(radar): 编排板块雷达状态"
```

## Task 3: Focused Radar Components

**Files:**

- Create: `frontend/src/components/radar/RadarToolbar.vue`
- Create: `frontend/src/components/radar/BoardRanking.vue`
- Create: `frontend/src/components/radar/BoardSnapshot.vue`
- Create: `frontend/src/components/radar/BoardStockTable.vue`
- Create: `frontend/tests/opportunity-radar-contract.test.js`

- [ ] **Step 1: Write failing component contract tests**

Read all four Vue files with `readFile` and assert:

```js
test('雷达工具栏提供类型切换、搜索、仅上涨和刷新', () => {
  assert.match(toolbar, /行业板块/)
  assert.match(toolbar, /概念板块/)
  assert.match(toolbar, /按板块名称筛选/)
  assert.match(toolbar, /仅看上涨/)
  assert.match(toolbar, /@click="\$emit\('refresh'\)"/)
})

test('板块和成分股错误只在各自组件中提供重试', () => {
  assert.match(ranking, /@retry="\$emit\('retry'\)"/)
  assert.match(stockTable, /@retry="\$emit\('retry'\)"/)
})

test('成分股操作具有可访问名称', () => {
  assert.match(stockTable, /查看.*详情/)
  assert.match(stockTable, /加入自选/)
})
```

- [ ] **Step 2: Run the contract test and verify RED**

Run: `cd frontend && node --test tests/opportunity-radar-contract.test.js`

Expected: FAIL because the radar component files do not exist.

- [ ] **Step 3: Implement `RadarToolbar.vue`**

Use `el-segmented` for industry/concept, a labeled `el-input` for search, `el-switch` for only-rising, and a refresh icon button with tooltip. Emit only `update:type`, `update:keyword`, `update:only-rising`, and `refresh`. All mobile controls must have a 44px minimum height.

- [ ] **Step 4: Implement ranking, snapshot and stock table**

- `BoardRanking` uses `StatusState` for initial loading, error and empty states; each board is a real `button` with `aria-pressed`.
- `BoardSnapshot` uses `formatPercent` and `formatYi`; missing metrics render `--` while real zero remains visible.
- `BoardStockTable` uses desktop table and compact mobile rows, 20-row pagination, `StockName`, and text+icon actions. It emits `open-stock`, `add-watchlist`, `retry`, and `page-change`.
- Signal meaning never relies only on color; every percentage includes its signed numeric text.

- [ ] **Step 5: Run contract tests and build**

Run: `cd frontend && node --test tests/opportunity-radar-contract.test.js && npm run build`

Expected: contract tests PASS and build exits 0.

- [ ] **Step 6: Commit checkpoint when authorized**

```bash
git add frontend/src/components/radar frontend/tests/opportunity-radar-contract.test.js
git commit -m "feat(radar): 构建雷达双栏组件"
```

## Task 4: Page Composition and Watchlist Action

**Files:**

- Create: `frontend/src/views/OpportunityRadar.vue`
- Modify: `frontend/tests/opportunity-radar-contract.test.js`

- [ ] **Step 1: Add a failing page contract test**

```js
test('机会雷达页面组合双栏组件并复用自选分组选择器', () => {
  assert.match(view, /class="radar-page workbench-page"/)
  assert.match(view, /workbench-page__header/)
  assert.match(view, /<BoardRanking/)
  assert.match(view, /<BoardStockTable/)
  assert.match(view, /<GroupPicker/)
  assert.match(view, /userStore\.requestLogin\(route\.fullPath\)/)
  assert.match(view, /watchlistStore\.addStockToGroup/)
})
```

- [ ] **Step 2: Run the page contract test and verify RED**

Run: `cd frontend && node --test tests/opportunity-radar-contract.test.js`

Expected: FAIL because `OpportunityRadar.vue` does not exist.

- [ ] **Step 3: Implement the page layout**

Compose the header, toolbar, two-column workspace, board list, board summary, stock table and `GroupPicker`. Desktop grid uses `minmax(320px, 40%) minmax(0, 60%)`; below 1024px it becomes one column. Keep the file below 300 lines by leaving request logic and detailed rendering in owned modules.

- [ ] **Step 4: Implement add-to-watchlist flow**

```js
function requestAdd(stock) {
  pendingStock.value = { code: stock.code, name: stock.name }
  if (!userStore.isLoggedIn) return userStore.requestLogin(route.fullPath)
  selectedGroupId.value = watchlistStore.activeGroup || watchlistStore.groups[0]?.id || ''
  pickerVisible.value = true
}

async function confirmAdd(groupId) {
  if (!pendingStock.value || adding.value) return
  adding.value = true
  try {
    const result = await watchlistStore.addStockToGroup(groupId, pendingStock.value)
    if (result.success) {
      ElMessage.success(`已加入「${result.groupName}」`)
      pickerVisible.value = false
      pendingStock.value = null
    } else if (result.reason === 'duplicate') {
      ElMessage.warning('该股票已在目标分组中')
    } else {
      ElMessage.error('加入自选失败')
    }
  } finally {
    adding.value = false
  }
}
```

- [ ] **Step 5: Run focused tests and build**

Run: `cd frontend && node --test tests/opportunity-radar*.test.js && npm run build`

Expected: radar tests PASS and build exits 0.

- [ ] **Step 6: Commit checkpoint when authorized**

```bash
git add frontend/src/views/OpportunityRadar.vue frontend/tests/opportunity-radar-contract.test.js
git commit -m "feat(radar): 组装机会雷达页面"
```

## Task 5: Route and Navigation Integration

**Files:**

- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/Layout.vue`
- Modify: `frontend/src/components/app/MobileNav.vue`
- Modify: `frontend/tests/layout-contract.test.js`
- Modify: `frontend/tests/opportunity-radar-contract.test.js`

- [ ] **Step 1: Write failing route and navigation tests**

```js
test('机会雷达注册为无需登录的懒加载一级路由', () => {
  assert.match(router, /path:\s*'\/radar'/)
  assert.match(router, /import\('\.\.\/views\/OpportunityRadar\.vue'\)/)
  assert.doesNotMatch(router, /path:\s*'\/radar'[\s\S]{0,180}requiresAuth:\s*true/)
})

test('桌面与移动导航提供雷达入口且移动列数跟随菜单', () => {
  assert.match(layout, /path:\s*'\/radar'.*title:\s*'雷达'/)
  assert.match(mobileNav, /--mobile-nav-columns/)
  assert.match(mobileNav, /items\.length/)
})
```

Also add `OpportunityRadar` to `viewNames` in `layout-contract.test.js`.

- [ ] **Step 2: Run tests and verify RED**

Run: `cd frontend && node --test tests/opportunity-radar-contract.test.js tests/layout-contract.test.js`

Expected: FAIL because the route and navigation entry are absent.

- [ ] **Step 3: Add route and menu item**

Add a lazy route named `OpportunityRadar` with title `机会雷达` and no `requiresAuth`. Insert `{ path: '/radar', title: '雷达', icon: 'Aim' }` after the board menu so the research flow remains market → board → radar → watchlist → reports.

- [ ] **Step 4: Make mobile navigation column count data-driven**

Bind `:style="{ '--mobile-nav-columns': items.length }"` on the nav and replace the fixed four-column declaration with:

```css
grid-template-columns: repeat(var(--mobile-nav-columns, 4), minmax(0, 1fr));
```

Verify five labels fit at 390px without truncating into adjacent items.

- [ ] **Step 5: Run full Node tests and build**

Run: `cd frontend && node --test tests/*.test.js && npm run build`

Expected: all tests PASS and production build exits 0. Existing chunk-size warnings may remain but no new build error is allowed.

- [ ] **Step 6: Commit checkpoint when authorized**

```bash
git add frontend/src/router/index.js frontend/src/components/Layout.vue frontend/src/components/app/MobileNav.vue frontend/tests
git commit -m "feat(radar): 接入雷达菜单与路由"
```

## Task 6: Browser Acceptance and Delivery Gate

**Files:**

- Modify only if failures identify an in-scope defect in radar files
- Evidence: `frontend/test-results/opportunity-radar-*.png`

- [ ] **Step 1: Start or confirm project services**

Use the unified frontend port only:

```bash
ss -ltnp | rg ':52764|:8000'
curl -fsS http://127.0.0.1:8000/health
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:52764/radar
```

Expected: frontend `52764` and backend `8000` listen; both HTTP checks succeed. Port `52765` is only the brainstorming companion and is not used for product acceptance.

- [ ] **Step 2: Run desktop, tablet and mobile smoke paths**

With Playwright temporary CLI and existing Chromium, verify at `1440x900`, `768x1024`, and `390x844`:

- industry list is sorted descending
- concept switch loads independently
- search and only-rising update the list
- selecting a board updates the stock pane
- stock pagination works when more than 20 rows exist
- stock detail navigation reaches `/stock/:code`
- no horizontal overflow or page errors
- touch controls are at least 44px on mobile

Save one full-page screenshot per viewport.

- [ ] **Step 3: Verify failure isolation and race behavior**

Use Playwright routing to inject:

- industry list `503` while concept succeeds
- one board stock request `503` while the ranking remains usable
- a delayed first board response followed by a fast second board response

Expected: errors stay local, retry restores data, and the delayed old response never replaces the second board.

- [ ] **Step 4: Verify themes and watchlist action**

Switch `ocean`, `jade`, and `charcoal`; verify readable selected state and涨跌 text. Use one uniquely named temporary user to verify group picker and add-to-watchlist. Before deletion, identify the exact username and user id; delete only that user's dependent records and verify zero matching temporary users remain.

- [ ] **Step 5: Run the final verification suite fresh**

```bash
cd frontend
node --test tests/*.test.js
npm run build
cd ..
backend/venv/bin/python -m unittest discover -s backend/tests -v
git diff --check
```

Expected: all frontend and backend tests PASS, build exits 0, and diff check produces no output.

- [ ] **Step 6: Perform final review**

Review the implementation against `docs/superpowers/specs/2026-08-30-opportunity-radar-design.md`. Treat missing failure states, stale-request protection, mobile overflow, inaccessible controls, or incomplete tests as delivery blockers.

- [ ] **Step 7: Commit final integration only when authorized**

```bash
git add frontend/src frontend/tests docs/superpowers/specs/2026-08-30-opportunity-radar-design.md docs/superpowers/plans/2026-08-30-opportunity-radar.md
git commit -m "feat(radar): 新增板块机会雷达"
```
