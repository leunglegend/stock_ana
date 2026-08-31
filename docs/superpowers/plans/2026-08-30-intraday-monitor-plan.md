# 盘中监控工作台 Implementation Plan

> 执行状态：已完成。后续补齐了真实抓取时间、市场降级元数据、行级重试和移动端错误详情；后端全量测试、前端全量契约测试与生产构建均已验证。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增需登录的 `/monitor` 盘中监控菜单和页面，并通过 `/api/monitor/overview` 一次返回市场环境、自选股快照、统一技术信号和行动队列。

**Architecture:** 后端新增 monitor schema、signal rules、聚合 service 和 route；聚合 service 按代码去重、受控并发读取一次 K 线并构造快照，按 60 秒缓存返回部分成功结果。前端新增独立 Monitor 页面和专用组件，桌面侧边栏、移动导航和路由守卫接入新入口；财务和 AI 详情继续复用现有按需接口。

**Tech Stack:** FastAPI、Pydantic v2、SQLAlchemy、AKShare、Vue 3、Vue Router、Pinia、Element Plus、Node `node:test`、Python `unittest/pytest`。

---

## 文件与职责映射

### 后端

- Create: `backend/app/schemas/monitor.py` — 监控接口请求参数、响应模型和内部 `MonitorSnapshot` 类型。
- Create: `backend/app/services/signal_rules.py` — MA/MACD/RSI/突破/回撤/成本规则及状态判定。
- Create: `backend/app/services/monitor_service.py` — 用户自选读取、代码去重、并发快照、缓存、市场环境、摘要和行动队列。
- Create: `backend/app/routes/monitor.py` — `/api/monitor/overview` 鉴权路由和参数校验。
- Modify: `backend/app/services/stock_data.py` — 暴露一次日 K 拉取并构造监控快照所需的内部 helper，复用现有指标计算逻辑。
- Modify: `backend/app/main.py` — 注册 monitor router。
- Create: `backend/tests/test_signal_rules.py` — 纯规则单元测试。
- Create: `backend/tests/test_monitor_service.py` — 聚合、去重、并发、缓存、降级和排序测试。
- Create: `backend/tests/test_monitor_route.py` — 鉴权、参数和用户隔离测试。

### 前端

- Create: `frontend/src/api/monitor.js` — `getMonitorOverview(params)` API 封装。
- Create: `frontend/src/views/Monitor.vue` — 页面状态、轮询、筛选、排序、选中项和按需详情调用。
- Create: `frontend/src/components/monitor/MonitorHeader.vue` — 分组选择、刷新、更新时间和数据延迟提示。
- Create: `frontend/src/components/monitor/MonitorMarketPulse.vue` — 指数、涨跌家数、涨跌停、成交额和市场环境。
- Create: `frontend/src/components/monitor/MonitorActionQueue.vue` — 高优先级行动项及跳转事件。
- Create: `frontend/src/components/monitor/MonitorTable.vue` — 桌面矩阵表格和移动紧凑列表。
- Create: `frontend/src/components/monitor/MonitorInspector.vue` — 选中股票信号、sparkline、财务快照和 AI 入口。
- Modify: `frontend/src/router/index.js` — 注册 `/monitor` 懒加载路由和 `requiresAuth`。
- Modify: `frontend/src/components/Layout.vue` — 桌面/移动菜单加入“盘中监控”。
- Create: `frontend/tests/monitor-contract.test.js` — 路由、菜单、API 和组件组合契约测试。
- Create: `frontend/tests/monitor-view-contract.test.js` — 加载、错误、轮询、筛选和无障碍契约测试。

### 文档

- Modify: `README.md` — 功能清单、API 表格和后续能力说明。

本功能不新增数据库表或字段。

## Task 1: 建立统一信号规则和响应模型

**Files:**
- Create: `backend/tests/test_signal_rules.py`
- Create: `backend/app/services/signal_rules.py`
- Create: `backend/app/schemas/monitor.py`

- [ ] **Step 1: 写规则失败测试**

在 `backend/tests/test_signal_rules.py` 构造包含前后两根 K 线的 `KLineItem` 列表，覆盖：

```python
def test_detects_trend_cross_rsi_breakout_and_cost_signals():
    rows = [
        KLineItem(date="2026-08-29", open=10, close=9.8, high=10.1, low=9.5,
                  volume=100, ma5=9.5, ma10=9.6, ma20=10.0,
                  dif=0.2, dea=0.3, rsi6=40),
        KLineItem(date="2026-08-30", open=10, close=10.8, high=10.9, low=9.9,
                  volume=180, ma5=10.4, ma10=10.1, ma20=10.0,
                  dif=0.5, dea=0.3, rsi6=78),
    ]

    result = analyze_signals(rows, cost_return_pct=-12.0)

    assert {item.code for item in result.signals} == {
        "trend-above-ma20", "macd-golden-cross", "rsi-overheated", "cost-loss"
    }
    assert result.status == "attention"

def test_returns_error_for_insufficient_kline():
    result = analyze_signals([], cost_return_pct=None)
    assert result.status == "error"
    assert result.signals == []
```

同时测试 `classify_market_environment` 的 `偏强`、`偏弱`、`分化`、`未知` 四种输入，以及 `build_action_queue` 对风险信号按 high/medium 排序。

- [ ] **Step 2: 运行失败测试**

Run: `cd backend && pytest tests/test_signal_rules.py -q`

Expected: FAIL，原因是 `signal_rules` 和 `monitor` schema 尚不存在。

- [ ] **Step 3: 实现最小规则模块**

在 `signal_rules.py` 定义稳定接口：

```python
def analyze_signals(rows: Sequence[KLineItem], cost_return_pct: float | None) -> SignalAnalysis: ...
def classify_market_environment(summary: MarketSummary | None) -> Literal["偏强", "偏弱", "分化", "未知"]: ...
def build_action_queue(items: Sequence[MonitorItem]) -> list[ActionQueueItem]: ...
```

沿用现有 `frontend/src/utils/stockSignals.js` 的阈值：RSI 75/25、近 20 日回撤 -10%、成本收益 +15%/-10%。规则函数的 `cost_return_pct`、`high20_distance_pct` 和区间收益均使用百分点，`-12.0` 表示 -12%。风险状态优先级为 `attention > strong > neutral`；数据不足的股票为 `error`。在 `schemas/monitor.py` 定义 `SignalItem`、`SignalAnalysis`、`MonitorQuote`、`MonitorIndicators`、`MonitorMetrics`、`MonitorItem`、`ActionQueueItem`、`MonitorSummary`、`MonitorMarket`、`MonitorOverview`、`MonitorError` 和内部 `MonitorSnapshot`，所有可缺失的行情/指标字段使用 Optional。

- [ ] **Step 4: 运行规则测试并提交独立变更**

Run: `cd backend && pytest tests/test_signal_rules.py -q`

Expected: PASS，且失败测试只覆盖当前任务新增规则。

Commit when authorized: `git add backend/app/schemas/monitor.py backend/app/services/signal_rules.py backend/tests/test_signal_rules.py && git commit -m "feat(monitor): 统一盘中信号规则"`

## Task 2: 增加一次 K 线快照能力和监控聚合 service

**Files:**
- Create: `backend/tests/test_monitor_service.py`
- Create: `backend/app/services/monitor_service.py`
- Modify: `backend/app/services/stock_data.py`

- [ ] **Step 1: 写聚合失败测试**

使用 fake watchlist rows、fake market summary 和可计数的 `fetch_snapshot`，验证：

```python
def test_deduplicates_codes_across_groups_and_returns_summary():
    stocks = [
        FakeWatchlistItem(id=1, group_id=10, group_name="重点", code="600519", name="贵州茅台", cost=1600),
        FakeWatchlistItem(id=2, group_id=11, group_name="观察", code="600519", name="贵州茅台", cost=1650),
        FakeWatchlistItem(id=3, group_id=10, group_name="重点", code="000001", name="平安银行", cost=0),
    ]

    result = build_monitor_overview(
        db=FakeSession(stocks), user_id=7, group_id="all", days=90,
        snapshot_loader=recording_loader, market_loader=lambda: market_summary,
    )

    assert recording_loader.calls == ["600519", "000001"]
    assert result.summary.stock_count == 3
    assert len(result.items) == 3
```

另测：单只 loader 抛异常仍返回其他 item；有旧缓存时 `stale=True`；空自选返回 200 语义的空 `MonitorOverview`；`group_id` 过滤和同一用户隔离；行动队列按风险优先级排序；缓存 TTL 内不重复调用 loader，过期后重新调用。

- [ ] **Step 2: 运行失败测试**

Run: `cd backend && pytest tests/test_monitor_service.py -q`

Expected: FAIL，原因是 `build_monitor_overview` 和快照 loader 尚未实现。

- [ ] **Step 3: 修改 stock_data 提供单次日 K 快照**

在 `backend/app/services/stock_data.py` 提取内部 helper，保持既有 `get_stock_info`、`get_kline_data` 行为不变：

```python
def get_monitor_snapshot(code: str, days: int = 90) -> MonitorSnapshot:
    """单次读取日 K，返回最新行情、指标、收益和 sparkline。"""
```

该 helper 复用现有 `_fetch_kline`、均线、MACD、KDJ、RSI 计算；从同一份 DataFrame 得到最新收盘价、前收盘涨跌、5/20 日收益和最近 30 个收盘点。返回的百分比字段统一使用百分点。无法取得有效 K 线时抛出可识别异常或返回带 error 的结果，不在此层做 HTTP 响应。

- [ ] **Step 4: 实现 monitor_service 聚合、缓存和排序**

定义公开函数：

```python
def build_monitor_overview(
    db: Session,
    user_id: int,
    group_id: str = "all",
    days: int = 90,
) -> MonitorOverview: ...
```

实现要求：

1. 查询属于 `user_id` 的分组和股票；`group_id != "all"` 时先验证分组归属，不存在抛出 `MonitorGroupNotFound`。
2. 按股票代码去重并保持首次出现顺序，但保留每个自选明细的 `watchlist_item_id`、分组、成本和备注，返回项数量仍按明细数统计。
3. 使用 `ThreadPoolExecutor(max_workers=4)` 或项目已有并发工具，对唯一代码调用一次 `get_monitor_snapshot`；主请求不得无限制创建线程。
4. 市场概览调用现有 `get_market_summary`，异常时返回 `environment="未知"` 并在顶层 `errors` 记录。
5. 计算 `relative_strength_vs_sh_pct = quote.change_pct - market.summary.sh_change_pct`，市场指数缺失时为 null；该字段使用百分点。
6. 使用 `signal_rules.analyze_signals` 生成 item 状态和信号；按 `attention`、`strong`、`neutral`、`error` 排序。
7. 只把风险信号和数据错误加入 `action_queue`，每项带 `code`、`name`、`priority`、`reasons`。
8. 快照缓存键为 `(code, days)`，TTL 60 秒；失败时优先返回最近缓存并标记 `stale=True`，无缓存则返回该项 `errors`。

- [ ] **Step 5: 运行 service 测试并提交独立变更**

Run: `cd backend && pytest tests/test_signal_rules.py tests/test_monitor_service.py -q`

Expected: PASS。

Commit when authorized: `git add backend/app/services/stock_data.py backend/app/services/monitor_service.py backend/tests/test_monitor_service.py && git commit -m "feat(monitor): 聚合自选股监控快照"`

## Task 3: 暴露 `/api/monitor/overview` 并完成后端契约测试

**Files:**
- Create: `backend/app/routes/monitor.py`
- Create: `backend/tests/test_monitor_route.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 写 route 失败测试**

使用 `TestClient(app)` 和 `app.dependency_overrides` 注入 fake current user/session，覆盖：

```python
def test_monitor_requires_authentication(client):
    response = client.get("/api/monitor/overview")
    assert response.status_code == 401

def test_monitor_rejects_invalid_days(authenticated_client):
    response = authenticated_client.get("/api/monitor/overview?days=45")
    assert response.status_code == 422

def test_monitor_returns_404_for_foreign_group(authenticated_client, monkeypatch):
    monkeypatch.setattr(monitor_service, "build_monitor_overview", raise_group_not_found)
    response = authenticated_client.get("/api/monitor/overview?group_id=99")
    assert response.status_code == 404
```

再验证成功响应的顶层字段包含 `as_of`、`market`、`summary`、`items`、`action_queue`、`errors`。

- [ ] **Step 2: 运行失败测试**

Run: `cd backend && pytest tests/test_monitor_route.py -q`

Expected: FAIL，原因是路由尚未注册。

- [ ] **Step 3: 实现路由和注册**

在 `backend/app/routes/monitor.py` 使用同步 `def` 路由，让 FastAPI 在线程池执行阻塞的 AKShare 聚合：

```python
router = APIRouter(prefix="/api/monitor", tags=["盘中监控"])

@router.get("/overview", response_model=MonitorOverview, summary="获取盘中监控总览")
def overview(
    group_id: str = Query("all", pattern=r"^(all|[0-9]+)$"),
    days: Literal[30, 60, 90] = Query(90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return monitor_service.build_monitor_overview(db, current_user.id, group_id, days)
    except MonitorGroupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
```

在 `backend/app/main.py` 导入并 `app.include_router(monitor_router)`，确保不会被前端 fallback 捕获。

- [ ] **Step 4: 运行后端回归测试并提交独立变更**

Run: `cd backend && pytest -q`

Expected: 全部 PASS。

Commit when authorized: `git add backend/app/routes/monitor.py backend/app/main.py backend/tests/test_monitor_route.py && git commit -m "feat(monitor): 暴露盘中监控接口"`

## Task 4: 接入前端 API、路由和菜单

**Files:**
- Create: `frontend/src/api/monitor.js`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/Layout.vue`
- Create: `frontend/tests/monitor-contract.test.js`

- [ ] **Step 1: 写前端契约失败测试**

在 `monitor-contract.test.js` 断言：

```js
assert.match(routerSource, /path:\s*['"]\/monitor['"]/)
assert.match(routerSource, /requiresAuth:\s*true/)
assert.match(layoutSource, /path:\s*['"]\/monitor['"][\s\S]*?title:\s*['"]盘中监控['"]/)
assert.match(apiSource, /getMonitorOverview/)
assert.match(apiSource, /\/monitor\/overview/)
```

同时读取 `Monitor.vue` 和 5 个 monitor 组件，确认文件存在且页面使用 `data-page-title`。

- [ ] **Step 2: 运行失败测试**

Run: `cd frontend && node --test tests/monitor-contract.test.js`

Expected: FAIL，原因是新 API、路由、菜单和页面文件尚不存在。

- [ ] **Step 3: 实现 API 封装和路由/菜单**

在 `frontend/src/api/monitor.js` 添加：

```js
import http from './http'

export function getMonitorOverview(params = {}) {
  return http.get('/monitor/overview', { params }).then((res) => res.data)
}
```

在 `router/index.js` 注册懒加载 `/monitor`，设置 `meta: { title: '盘中监控', requiresAuth: true }`。在 `Layout.vue` 的 `navBlueprint` 中把 `{ path: '/monitor', title: '盘中监控', compactTitle: '监控', icon: 'Monitor' }` 放在市场之后；`resolveNavId` 返回 `monitor`。如果 Element Plus 图标导出不含 `Monitor`，统一替换为已注册的 `DataLine`，不要在模板中动态引入未注册图标。

- [ ] **Step 4: 运行契约测试并提交独立变更**

Run: `cd frontend && node --test tests/monitor-contract.test.js`

Expected: PASS。

Commit when authorized: `git add frontend/src/api/monitor.js frontend/src/router/index.js frontend/src/components/Layout.vue frontend/tests/monitor-contract.test.js && git commit -m "feat(monitor): 接入盘中监控菜单"`

## Task 5: 实现 Monitor 页面和专用展示组件

**Files:**
- Create: `frontend/src/views/Monitor.vue`
- Create: `frontend/src/components/monitor/MonitorHeader.vue`
- Create: `frontend/src/components/monitor/MonitorMarketPulse.vue`
- Create: `frontend/src/components/monitor/MonitorActionQueue.vue`
- Create: `frontend/src/components/monitor/MonitorTable.vue`
- Create: `frontend/src/components/monitor/MonitorInspector.vue`
- Create: `frontend/tests/monitor-view-contract.test.js`

- [ ] **Step 1: 写页面契约失败测试**

在 `monitor-view-contract.test.js` 断言页面包含：

```js
assert.match(viewSource, /class="[^"]*monitor-page[^"]*workbench-page/)
assert.match(viewSource, /data-page-title[^>]*>盘中监控</)
assert.match(viewSource, /getMonitorOverview/)
assert.match(viewSource, /setInterval|onInterval|refreshTimer/)
assert.match(viewSource, /MonitorActionQueue/)
assert.match(viewSource, /MonitorTable/)
assert.match(viewSource, /MonitorInspector/)
assert.match(tableSource, /aria-label|role="button"/)
assert.match(actionQueueSource, /open-stock|emit\(['"]open-stock/)
```

- [ ] **Step 2: 运行失败测试**

Run: `cd frontend && node --test tests/monitor-view-contract.test.js`

Expected: FAIL，原因是页面和组件尚未创建。

- [ ] **Step 3: 实现无请求副作用的展示组件**

组件只通过 props 接收数据，通过 emits 向页面传递动作：

- `MonitorHeader`：`groups`、`activeGroupId`、`loading`、`asOf`、`stale`；emit `update:groupId`、`refresh`。
- `MonitorMarketPulse`：`market`、`summary`；文本展示 `environment`、指数和涨跌停，不以颜色作为唯一表达。
- `MonitorActionQueue`：`items`；emit `open-stock(code)`，同时显示 priority、reason。
- `MonitorTable`：`items`、`loading`、`selectedCode`、`filters`；emit `select`、`open-stock`、`retry`。
- `MonitorInspector`：`item`、`financial`、`financialState`、`aiAdvice`、`aiState`；emit `open-stock`、`start-analyze`。

表格桌面端使用现有 Element Plus 表格/按钮风格和项目 `workbench` 样式；移动端使用紧凑列表或抽屉，不新增圆角卡片主题。

- [ ] **Step 4: 实现 Monitor.vue 状态和数据流**

页面维护：

```js
const overview = ref(null)
const selectedCode = ref(route.query.code || '')
const groupId = ref('all')
const filters = reactive({ keyword: '', status: 'all', onlyActionable: false, sortBy: 'status' })
```

实现 `loadOverview({ silent = false } = {})` 调用 `getMonitorOverview({ group_id: groupId.value, days: 90 })`；刷新期间保留旧数据。用 `onMounted`/`onUnmounted` 管理 60 秒定时器，并用 request generation 或 AbortController 忽略旧响应。交易时段判断沿用前端时区 `09:30–11:30`、`13:00–15:00`；非交易时段不启动轮询。

过滤和排序只作用于已返回的 `items`：关键词匹配代码/名称，状态过滤，行动过滤，排序支持状态严重度、涨跌幅、相对强弱、信号数量。选中项不存在时自动选中第一项或清空。

检查器选择股票后按需调用 `getFinancialData(code)`；AI 仅由用户点击触发，沿用现有 `analyzeStock` SSE 封装或提取现有逻辑，不在 `loadOverview` 中自动调用。

- [ ] **Step 5: 运行页面契约测试并提交独立变更**

Run: `cd frontend && node --test tests/monitor-contract.test.js tests/monitor-view-contract.test.js`

Expected: PASS。

Commit when authorized: `git add frontend/src/views/Monitor.vue frontend/src/components/monitor frontend/tests/monitor-view-contract.test.js && git commit -m "feat(monitor): 实现盘中监控工作台"`

## Task 6: 补齐错误状态、移动端行为和文档

**Files:**
- Modify: `frontend/src/views/Monitor.vue`
- Modify: `frontend/src/components/monitor/MonitorHeader.vue`
- Modify: `frontend/src/components/monitor/MonitorTable.vue`
- Modify: `frontend/src/components/monitor/MonitorInspector.vue`
- Modify: `frontend/tests/monitor-view-contract.test.js`
- Modify: `README.md`

- [ ] **Step 1: 写边界状态测试契约**

增加断言：

```js
assert.match(viewSource, /StatusState/)
assert.match(viewSource, /cloudError|errors|partial|stale/)
assert.match(viewSource, /router\.push\(['"]\/stock\//)
assert.match(headerSource, /更新|刷新/)
assert.match(tableSource, /重试|retry/)
```

- [ ] **Step 2: 实现状态分层和可访问性**

页面实现四类状态：

1. 首次加载且无数据：`StatusState loading`。
2. 整体请求失败：`StatusState error` + 重试。
3. 无自选股：`StatusState empty` + 跳转 `/watchlist`。
4. 已有数据但部分失败/过期：保留可用项，在行级和页头展示 `stale`、错误原因和单只重试。

给刷新按钮、更新时间和队列变更增加 `aria-live="polite"`；表格行的选中状态同时提供文本或 `aria-selected`；键盘可聚焦的股票入口使用按钮或 RouterLink，不依赖颜色区分涨跌。

- [ ] **Step 3: 验证移动端和返回状态**

移动端隐藏桌面检查器，使用抽屉/底部面板展示选中项；菜单保持横向滚动。跳转个股详情时把当前 `group_id`、筛选字段和 `code` 写入 query，返回 `/monitor` 时从 query 恢复选中股票和筛选。

- [ ] **Step 4: 更新 README**

在功能清单加入“盘中监控”，在 API 表格加入：

```text
盘中监控总览 | GET | /api/monitor/overview | 需登录 | 市场环境、自选股快照、技术信号、行动队列
```

补充说明：数据为定时刷新/缓存降级结果，不是逐笔实时行情；第一期不计算仓位和总资产。

- [ ] **Step 5: 运行前端测试和构建并提交独立变更**

Run: `cd frontend && node --test tests/monitor-contract.test.js tests/monitor-view-contract.test.js && npm run build`

Expected: 契约测试 PASS，Vite build 成功。

Commit when authorized: `git add frontend/src/views/Monitor.vue frontend/src/components/monitor frontend/tests/monitor-view-contract.test.js README.md && git commit -m "feat(monitor): 完善监控状态与文档"`

## Task 7: 最终整合验证

**Files:**
- Test only: `backend/tests/test_signal_rules.py`, `backend/tests/test_monitor_service.py`, `backend/tests/test_monitor_route.py`, `frontend/tests/monitor-contract.test.js`, `frontend/tests/monitor-view-contract.test.js`

- [ ] **Step 1: 运行后端全量测试**

Run: `cd backend && pytest -q`

Expected: 所有后端测试 PASS。

- [ ] **Step 2: 运行前端全量契约测试和构建**

Run: `cd frontend && node --test tests/*.test.js && npm run build`

Expected: 所有 Node 契约测试 PASS，Vite build 成功。

- [ ] **Step 3: 做手动 smoke 检查**

启动后端和前端，验证：

1. 未登录访问 `/monitor` 会弹登录并在登录后回跳。
2. 登录后 `/monitor` 菜单在桌面侧边栏和移动导航均高亮。
3. 有 2 个分组且同一股票重复时，接口只产生一次股票数据请求。
4. 单只股票数据失败时，其他行和市场摘要仍显示。
5. `stale` 数据有延迟提示，且页面不称其为实时。
6. 点击行动项可进入个股详情，返回后仍保留监控筛选。

- [ ] **Step 4: 交付前检查变更范围**

Run: `git status --short && git diff --stat`

确认只包含本功能相关的新增/修改文件；不覆盖工作区原有用户改动，不删除数据库或历史文件。
