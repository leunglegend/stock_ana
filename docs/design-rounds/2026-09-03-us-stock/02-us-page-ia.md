# 美股页面 + Dashboard 卡片 — 前端 IA 与组件结构设计

- 日期：2026-09-03
- 范围：只读调研产出的前端信息架构（IA）与组件拆解设计（产品决策轮）
- 性质：设计候选，不落业务代码
- 数据层可行性：由另一条设计线负责，本文默认后端能提供"美股指数 / 板块涨跌 / 板块成分股"三类数据，不纠结具体数据源
- 结论速览：两套候选页面 IA（方案 A「完整板块工作台」/ 方案 B「今日主线复盘」），共享同一批新组件；推荐以方案 A 为骨架、在其顶部叠加"复盘摘要带"（吸收方案 B 的叙事元素）。

---

## 1. 现有页面与组件惯例摘要（新页面沿用的基线）

阅读对象：`frontend/src/views/{Dashboard,BoardMonitor,OpportunityRadar,StockDetail}.vue`、`components/{board,dashboard,radar,app,base}/*`、`router/index.js`、`style.css`、`composables/*`。

### 1.1 页面壳与布局分层

- 所有页面用 `<div class="xxx-page workbench-page">` 包裹；`.workbench-page` 是**单列 CSS grid**（`display:grid; gap:var(--spacing-2)`，见 `style.css:119`）。
- 页面头 `.workbench-page__header`：左侧 `h1[data-page-title]` + 右侧动作按钮（如 Dashboard 的"刷新 / 板块全景"）；`afterEach` 会把焦点移到 `[data-page-title]`，用于无障碍与路由过渡。
- 工具条 `.workbench-toolbar`：放 `el-tabs` + 筛选输入 + `el-select` 排序 + `el-pagination`（BoardMonitor 最典型）。
- 工作区 `.workbench-grid` / `.workbench-grid--primary`（3fr:2fr）/ `--reader`：主从两栏，面板之间用 `gap:0 + 内部分隔线`拼成一个带边框的大工作台。
- 数据摘要用「横条 strip」：OpportunityRadar 的 `.radar-page__summary-strip`（4 格 label+大数字）。Dashboard 用 `.dashboard-page__market-pulse`（把指数与广度并成一个 6 列、88px 高的脉冲条）。
- AI 摘要用底部「通栏带」：`MarketAiSummary`（label + 单行文本 + "展开研究"按钮），Dashboard 放在最底部。
- 各页在 `<768px` 会把 header/工作区切单列，表格行退化为卡片行（详见 1.5 响应式）。

### 1.2 组件分层（可复用资产）

| 层级 | 目录 | 说明 |
|---|---|---|
| 页面编排 | `views/*.vue` | 只做组装与路由/query 状态；数据交给 composable |
| 业务块 | `components/{board,dashboard,radar,monitor,stock,us?}/` | 域内面板 |
| 原子/基础 | `components/base/` | `SectionPanel`、`StatusState`、`PercentageDisplay`、`PriceDisplay`、`MetricCell`、`StockName`、`TagBadge` |
| 应用骨架 | `components/app/` | `DesktopSidebar`、`MobileNav`、`CommandBar` |
| 数据 | `composables/*` + `api/*.js` | `useAsyncSection`、`useDashboardMarket`、`useOpportunityRadar` |

关键可复用基础组件与用法：

- `SectionPanel`（`variant: standard/flush/overlay`，slot：header/body/footer）：工作台面板**统一方形边框、radius 0、无投影**；`flush` 表示 body 无内边距（专放表格/行列表）。
- `StatusState`（`state: loading/empty/error` + `min-height` + `@retry`）：所有区块的加载/空/错三态统一出口。
- `PercentageDisplay`（`+1.23%` 红/绿/灰，`size sm/md/lg`）、`PriceDisplay`（价格 + 涨跌额 + 涨跌幅）、`MetricCell`（label + 大数字）、`StockName`（名称 + 代码，代码用 mono 小字）、`TagBadge`。
- 涨跌语义统一走 token：涨用 `--text-positive`、跌用 `--text-negative`，数字一律 `font-family: var(--font-family-mono)` + `font-variant-numeric: tabular-nums`。
- 视觉决策点：美股本土是"绿涨红跌"，但本平台用户习惯 A 股"红涨绿跌"；**建议美股页沿用平台涨跌色语义（涨=--text-positive，跌=--text-negative）**，保持产品内一种语义，只在文案（如"美股收盘"角标）区分市场。

### 1.3 板块页主从交互范式（核心参照：BoardMonitor + BoardDetailPanel）

- 页面 = 顶部工具条 + `.workbench-grid--primary` 工作台（左：板块表；右：详情面板）。
- 左表 `BoardTable`：`<button>` 行（不是 el-table），行内含"名称+描述/领涨股+上涨/下跌家数"与"成交额/换手/涨跌幅"；点击 `@select`。
- 右侧 `BoardDetailPanel`：桌面用 `SectionPanel` 常驻右栏，**移动端自动切换 `ElDrawer`（direction: btt, size: 100%）**；组件内部用 `detailContainer = mobile ? ElDrawer : SectionPanel` 动态容器，是"同一份内容两容器"的现成范式。
- 空态引导：右栏未选中时显示 `StatusState(state=empty, "选择一个板块查看成分股")`。
- 选中板块即拉成分股 `getBoardStocks(type, name)`，本地筛选/排序/分页（`detailPageSize=10`）。
- 点击成分股 → `router.push('/stock/' + code)`（A 股数字代码）。
- **路由同步**：当前板块/类型写进 query（`/board?type=industry&name=xx`），刷新/深链可还原；列表 `watch` route 变化触发还原。这是"Dashboard 卡片深链到板块详情"的现成机制。
- 列表排序为本地操作（全量拉回后 FE 排），板块接口不分页。

### 1.4 Dashboard 组织（Dashboard.vue + useDashboardMarket）

DOM 顺序：header（含"板块全景"主按钮）→ `SectionPanel` 全宽市场脉冲条（`MarketIndices` + `MarketBreadth` 并排 6 列）→ `.workbench` 双栏（左 `TopBoards`，右 `WatchlistSnapshot` + `MarketBreadthFacts`）→ 底部 `MarketAiSummary` 通栏。

- 卡片一律是 `SectionPanel variant="flush"`（方形），header 内嵌标题 + `el-button link` "查看全部"。
- 数据由 `useDashboardMarket` 统一编排：`useAsyncSection` 管理 loading/error、30s 定时刷新、SSE 逐字拼接 AI 摘要、请求代际（requestId）防串号。
- 跳转约定：Dashboard 内 `openBoard` → `router.push({path:'/board', query:{type, name}})`；`openStock` → `/stock/:code`。

### 1.5 响应式约定

- `useResponsive`：`isMobile(<768)` / `isTablet(768-1023)` / `isDesktop(>=1024)`；部分页用 `isCompact = !isDesktop` 统管平板+手机。
- 断点 CSS：`>=1024` 桌面网格；`768-1023` 主从并栏塌成单列（详情区排到列表上方或变抽屉）；`<768` header 转网格、工具栏控件占满、表格列头隐藏改卡片行。
- 移动导航条 `MobileNav` 与桌面侧栏 `DesktopSidebar` 共用同一份 `items`。

### 1.6 路由与导航注册点

- 路由在 `frontend/src/router/index.js`：一级页带 `meta:{title, icon}`；`StockDetail/ReportDetail` 等为 `meta.hidden` 子页。登录保护用 `meta.requiresAuth`。
- 导航项**不在路由里**，而是 `Layout.vue` 的 `navBlueprint` 数组（含 `path/title/compactTitle/icon`）+ `resolveNavId()` 映射到 `id`；`DesktopSidebar.isActive` / `MobileNav.isActive` 靠 `id` 判断高亮（前缀匹配：`/reports/*`、`/stock/*`）。
- 因此新增"美股"页要改 3 处：`router/index.js` 加路由、`Layout.vue` `navBlueprint` 加项、两个 isActive 函数（若有子路径）加前缀匹配。

### 1.7 数据与 API 惯例

- `api/*.js` 用 `http`（axios）封装，函数返回 `res.data`；板块/行情接口目前塞在 `api/stock.js`（新业务建议独立 `api/us.js`）。
- 端点风格：`GET /api/board/industry|concept` → `List[BoardInfo]`；`GET /api/board/{type}/{name}/stocks` → `List[BoardStock]`；`GET /api/board/market/summary` → `MarketSummary`；AI 摘要为 SSE：`GET /api/board/market/ai-summary`（`[DONE]` 收尾）。
- 字段 snake_case：`change_pct / change_amount / total_turnover / turnover_rate / leading_stock / leading_change / rise_count / fall_count / stock_count`。板块成分股 `BoardStock{code,name,price,change_pct,change_amount,turnover_rate,pe,total_mv}`。
- 单页数据获取用 `useAsyncSection(fetcher, {initialData})`；跨页/轮询用页面级 composable。

---

## 2. 新能力的目标信息架构总览

产品主诉求：**美股收盘后复盘：看今天指数/板块/个股谁在涨跌**；主路径是"指数 → 涨的行业板块 → 板块里领涨领跌个股"。

目标用户主路径（本文按此设计页面 IA 与跳转）：

```
Dashboard「美股摘要」卡片
   │  点击卡片 / "进入美股复盘"
   ▼
「美股复盘」页
   ├─ ① 指数与广度一眼态（道指/标普/纳指 + 涨跌家数）
   ├─ ② 板块涨跌榜（领涨/领跌 或 TopN）
   │     │ 点击某板块
   │     ▼
   │   板块详情（板块事实 + 成分股按涨跌幅排序，看领涨领跌个股）
   ▼
（二期扩展口）A 股联动映射 / 美股个股详情页 / 加入自选
```

约束与留口（本期不做，结构预留）：
- A 股联动映射二期：在板块详情、成分股行上预留"联动 A 股"动作位与路由 query 扩展。
- 美股个股详情：现有 `/stock/:code` 与后端 `stock.py` 是 A 股逻辑（6 位数字代码），美股 ticker 是字母（AAPL），**不能复用**；本期成分股行点击不进入 A 股个股页，预留 `/us/stock/:symbol` 二期路由。

---

## 3. 路由与入口设计

### 3.1 主路由（两个方案共用）

```js
{
  path: '/us',
  name: 'UsMarket',
  component: () => import('../views/UsMarket.vue'),
  meta: { title: '美股复盘', icon: 'Globe' },
}
```

- 侧栏/移动导航文案建议："美股"（compactTitle 复用"美股"）；位置建议放在"板块监控"与"机会雷达"之间（与板块类工具相邻），最终由产品定。
- `Layout.vue` `navBlueprint` 追加：`{ path: '/us', title: '美股', icon: 'Globe' }`；`resolveNavId` 加 `if (path === '/us') return 'us'`；两个 `isActive` 加 `if (item.id === 'us') return route.path === '/us' || route.path.startsWith('/us/')`（为二期子路由预留）。

### 3.2 页面内状态与深链约定（对齐 BoardMonitor）

- 选中板块用 query 表达：`/us?sector=<板块名>`（URL 编码），刷新可还原；关闭详情则替换回 `/us`。
- 方案 A 额外 `?tab=leaders|laggards`（板块榜方向）可选项；方案 B 可无额外 query。
- Dashboard 卡片上的"领涨板块第一名"可深链：`router.push({ path:'/us', query:{ sector: name } })`。

### 3.3 二期扩展路由（本期不实现，仅预留命名空间）

```js
// 二期：美股个股详情（占位）
{ path: '/us/stock/:symbol', name: 'UsStockDetail', meta: { hidden: true } }
// 二期：A 股联动映射结果位
// 在 UsMarket 上通过 query ?map=A 进入联动态
```

---

## 4. 方案 A：完整板块工作台（对齐现有 A 股板块页）

定位：把现有 `板块监控`（BoardMonitor）的成熟主从范式搬到美股，并在顶部加"复盘摘要条"。信息最全、上手成本最低（老用户零学习）。

### 4.1 页面结构示意（桌面文本线框）

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 美股复盘                                    [数据时间 美东09-02 16:00] [刷新]│   ← workbench-page__header
├──────────────────────────────────────────────────────────────────────────┤
│  道琼斯   34,850.20 +1.05% │ 标普500  4,512.30 +0.72% │ 纳斯达克 14,032.11 +1.18% │ 涨/跌家数 3210/4820 │  ← 复盘摘要条(4格)
├──────────────────────────────────────────────────────────────────────────┤
│ [AI 复盘一句话: 科技与半导体领涨，能源领跌…]            [展开研究]            │   ← 可选 AI 通栏带(复用 MarketAiSummary)
├────────────────────────────────────────────────────────┬─────────────────┤
│  行业板块 · 领涨榜          关键字🔍                    │   板块详情       │
│  ─────────────────────────                              │                 │
│  ▸ 半导体      领涨 NVDA · 涨 32/跌 8   +3.42%         │   [当前为空态]   │
│  ▸ 科技软件    领涨 MSFT · 涨 45/跌 12  +2.10%         │  "选择左侧板块    │
│  ▸ 消费电子    领涨 AAPL · 涨 28/跌 15  +1.34%         │   查看成分股涨跌" │
│  ▸ 能源       领跌 XOM  · 涨 6/跌 22   -1.80%  …       │                  │
│  ▸ 金融       领跌 JPM  · 涨 14/跌 26  -0.95%  …       │                  │
│  …（领涨/领跌 切换 tab，本地排序，分页 10/页）            │                  │
└────────────────────────────────────────────────────────┴─────────────────┘
```

选中板块后右侧展开：

```
┌ 板块详情 ────────────────────────────── 半导体  +3.42%  [×] ┐
│ 领涨股 NVDA +4.1% │ 涨/跌 32/8 │ 成分股 48 │ 成交额 $xx亿    │   ← 板块事实(5格)
├────────────────────────────────────────────────────────────┤
│ [筛选名称或代码 🔍] [排序: 涨跌幅 ▾]                          │
│  NVDA  英伟达    $468.3  +4.10%   成交额 …                  │   ← 成分股行(button)
│  AMD   超威      $127.1  +3.25%   …                         │
│  …  点击行 → 二期 /us/stock/:symbol（本期禁用/提示）          │
│  ⏴ 上一页  1/5  ⏵                                            │
└────────────────────────────────────────────────────────────┘
```

### 4.2 交互层级与状态

1. 层级：指数/广度（一眼态，不点击）→ 板块榜（点击选中）→ 板块详情右栏（点成分股 → 二期个股）。
2. 榜单位置即"领涨/领跌"：用 `el-tabs` 领涨榜（涨幅降序）| 领跌榜（涨幅升序），同一份板块数据本地排序，不重复请求。
3. 详情右栏桌面常驻、移动端 btt 抽屉（复用 BoardDetailPanel 容器切换范式）。
4. 数据加载：`useUsMarket` 拆 `summarySection` + `sectorsSection`；成分股为点击时单发请求，带请求代际防串号；可加 30s 轮询（收盘复盘场景也可不做轮询，改为手动刷新 + 进入时拉一次）。
5. 路由同步：选中板块写 `?sector=`，刷新还原。

### 4.3 上手成本

- 对已在用 A 股板块页的老用户：几乎零成本，交互一一对应，只是数据换成美股。
- 对美股新手：顶部摘要条给出当日强弱；完整板块榜便于横向比较，但首屏信息密度高。
- 对产品/开发：实现风险最低（复刻现有范式、复用组件多），首屏请求仅 2 个接口。

---

## 5. 方案 B：今日主线复盘（极简流）

定位：为"收盘后 3 分钟回顾"设计，一屏讲清"今天的主线是谁"。只给 TopN + 下钻，不做常驻主从工作台。

### 5.1 页面结构示意（桌面文本线框）

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 美股复盘 · 今日主线                            [美东09-02 收盘] [刷新]    │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌──────────┐                                │
│ │ 道琼斯    │  │ 标普500   │  │ 纳斯达克  │      涨 3210 / 跌 4820        │  ← 3张大指数卡 + 广度
│ │ +1.05%   │  │ +0.72%   │  │ +1.18%   │      （新高 45 / 新低 28）      │
│ │ 34,850.20│  │ 4,512.30 │  │ 14,032.11│                                │
│ └──────────┘  └──────────┘  └──────────┘                                │
├──────────────────────────────────────────────────────────────────────────┤
│ 🤖 今日主线：资金聚焦科技，半导体(NVDA+4.1%)领涨，能源受油价拖累领跌。    │  ← AI 一句话主线(通栏)
├──────────────────────────────────────────┬───────────────────────────────┤
│ 领涨板块 Top5                             │ 领跌板块 Top5                 │
│  1 半导体        +3.42%  领涨 NVDA        │  1 能源        -1.80% 领跌 XOM │
│  2 科技软件      +2.10%  领涨 MSFT        │  2 房地产      -1.12% 领跌 PLD │
│  3 消费电子      +1.34%  领涨 AAPL        │  3 公用事业    -0.64% 领跌 NEE │
│  4 …                                      │  4 …                          │
│  5 …                                      │  5 …                          │
│                              [查看全部板块 →]                              │  ← 低频出口(可选:跳 /us 全量或弹层)
├──────────────────────────────────────────┴───────────────────────────────┤
│ 点击任一板块 → 底部/右侧抽屉：                                             │
│  半导体 +3.42% │ 领涨 NVDA +4.1% │ 涨/跌 32/8                              │
│  领涨 Top5: NVDA +4.1 · AMD +3.2 · …       领跌 Top5: …                   │
└──────────────────────────────────────────────────────────────────────────┘
```

移动端：3 张指数卡纵向堆叠，两块 Top5 上下排列，点板块弹 btt 全高抽屉。

### 5.2 交互层级与状态

1. 层级：指数 + 广度（一眼态）→ AI 一句话主线（引导叙事）→ 领涨/领跌 TopN（两个对照面板）→ 点板块弹层下钻成分股 Top 涨跌 → （二期）点个股。
2. 下钻形态与 A 不同：不是"左表右详情"常驻，而是**抽屉/浮层**（桌面 rtl 抽屉或居中浮层、移动 btt 全高），看完即关，回到主线视图。
3. 组件复用：TopN 面板就是 `UsSectorTable` 喂两段 slice（领涨 5 / 领跌 5）；抽屉内容就是 `UsSectorDetailPanel` 以 `compact` 模式渲染（默认只列领涨/领跌 Top5，可展开"全部成分股"分页）。
4. 板块榜方向天然分裂在左右两栏，不需要排序器/分页，工具栏最简（仅刷新 + 日期）。
5. "查看全部板块"低频出口：跳 `/us?view=all`（方案 A 形态）或抽屉内翻页；避免极简视图把深度浏览堵死。

### 5.3 上手成本

- 完全不懂板块页的新用户：路径最短、信息即结论（"谁在涨、谁在跌"），上手成本最低。
- 美股新手：AI 一句话主线降低读表门槛，符合"复盘"心智。
- 重度/老用户：无常驻全量榜，要翻全部板块多一步；习惯工作台主从的老用户会觉得"不能边选边看"。
- 对开发：交互形态（桌面抽屉）比方案 A 略新，但组件集合与方案 A 高度重合，额外成本主要在页面装配与 compact 态。

---

## 6. Dashboard 美股摘要卡片

### 6.1 放哪、长什么样

Dashboard（A 股市场概览）当前结尾是 `MarketAiSummary` 通栏。建议在 AI 通栏**之下**追加一条全宽 `SectionPanel`（与 `TopBoards` 同款方形面板），作为"跨市场"附卡，避免抢占 A 股主内容。若产品希望美股在 A 股开盘前更显眼，可改为放在市场脉冲条与 workspace 之间（位置取舍见 6.4）。

文本线框图（桌面，全宽条）：

```
┌ 美股收盘 · 09-02 (美东)                         [进入美股复盘 →]        ┐
│  ┌ 道琼斯 34,850.20 +1.05% ┐ ┌ 标普500 4,512.30 +0.72% ┐ ┌ 纳指 14,032.11 +1.18% ┐ │
│  └─────────────────────────┘ └─────────────────────────┘ └──────────────────────┘ │
│  领涨板块  ▸ 半导体 +3.42% · 科技软件 +2.10%     领跌板块  ▸ 能源 -1.80% · 房地产 -1.12% │
│  涨 3210 / 跌 4820 · 数据时间 04:00（北京时间）                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 最小信息集

| 内容 | 是否要 | 理由 |
|---|---|---|
| 三大指数收盘值 + 涨跌幅（道指/标普/纳指） | 必选 | 一屏回答"美股今天收成怎样"，复用 `PriceDisplay` 3 联 |
| 涨 / 跌 家数（广度） | 推荐 | 一句话回答"今天是普涨还是普跌"；数据缺时降级隐藏 |
| 领涨板块 Top2-3 + 涨跌幅 | 必选 | 回答"钱去了哪"，也是卡片→页面深链入口 |
| 领跌板块 Top1-2 + 涨跌幅 | 必选 | 回答"谁在拖后腿" |
| 数据时间戳（美东收盘/北京时间） | 必选 | 复盘必须锚定"哪一天/何时" |
| 一句 AI 摘要 | 不建议放卡片 | 理由见 6.3 |

### 6.3 "一句 AI 摘要是否要"：放页面不放卡片

- AI 摘要是 SSE 逐字生成，有延迟且有成本；卡片是"一眼态"，放文本会顶高卡片、造成跳变。
- 美股页内已有 AI 主线通栏（方案 B 必选、方案 A 可选）。卡片点击即跳页，摘要的"叙事"在页内承接更合适。
- 若产品坚持卡片也有，建议只显示后端缓存的上一句结论（非实时生成），单行截断 + 进入页面展开。

### 6.4 交互与位置

- 整卡 header 右侧放 `el-button link type=primary` "进入美股复盘 →"，点击 `router.push('/us')`；板块芯片点击可深链 `/us?sector=半导体`。
- 数据源：一个接口 `getUsSummary()`（含指数+广度+Top 涨跌板块），避免卡片依赖多个请求；由 `useDashboardMarket` 同级新增 `useUsCard()`（或并入同一 composable）拉取，可跟随 30s 轮询（美股闭市后数据不常变，轮询可放宽到 5-10 分钟或只手动刷新）。
- 折叠态：移动端（<768）仅展示 3 指数行 + 领涨/领跌板块第一行，其余隐藏。

---

## 7. 组件拆解清单

两个方案**共用同一批新组件**，差异只在"页面装配方式 / 详情容器 / 是否 compact"。下表标注各组件在 A / B 的使用方式。

### 7.1 新建 .vue 组件

建议新目录 `frontend/src/components/us/`。

| 组件 | 职责 | 方案 A | 方案 B | 关键 props/emits |
|---|---|---|---|---|
| `views/UsMarket.vue` | 页面编排：header、摘要区、主区/极简双栏、抽屉，路由/query 同步 | 用 | 用 | — |
| `components/us/UsIndexStrip.vue` | 指数一眼态：3 大指数（可配）价格+涨跌幅卡片条；含 `as_of` 徽标 | 用（顶部 4 格摘要条的一部分） | 用（3 张大卡+广度） | `indices[]`、`breadth` |
| `components/us/UsBreadth.vue` | 涨/跌家数、新高/新低等广度格（内部用 `MetricCell`） | 用 | 用（合并进指数条/独立） | `summary` |
| `components/us/UsSectorTable.vue` | 板块涨跌行列表（可喂全量或 TopN slice）；名称+领涨 symbol+涨跌家数+涨跌幅；含 loading/error/empty（`StatusState`） | 左栏全量 + 领涨/领跌 tab | 领涨 Top5 / 领跌 Top5 两块 | `title`、`rows[]`、`direction`、`selectedName`；emit `select/retry` |
| `components/us/UsSectorDetailPanel.vue` | 板块下钻：facts 带 + 成分股涨跌列表 + 筛选/排序/分页；桌面 SectionPanel / 移动端 btt Drawer 容器切换；支持 `compact`（默认 TopN 涨跌两段，可展开全量） | 常驻右栏 | 抽屉/浮层 | `visible/loading/error/mobile/board/stocks`、`compact`；emit `close/retry/open-symbol` |
| `components/dashboard/UsSnapshotCard.vue` | Dashboard 摘要卡片：3 指数、涨跌家数、领涨/领跌板块芯片、时间戳、跳转 | Dashboard | Dashboard | `summary/loading/error`；emit `retry/open` |

### 7.2 复用的现有组件（不新建）

| 现有组件 | 用途 |
|---|---|
| `base/SectionPanel.vue` | 页面各面板容器（flush 放表格） |
| `base/StatusState.vue` | 各区块 loading/empty/error |
| `base/PriceDisplay.vue` | 指数/个股价格+涨跌 |
| `base/PercentageDisplay.vue` | 涨跌幅徽标 |
| `base/MetricCell.vue` | 广度/事实格大数字 |
| `base/StockName.vue` | 成分股"名称+ticker"（code 传 `AAPL` 这类 symbol 即可，无需新建；二期如需交易所前缀再做 `UsSymbol` 变体） |
| `base/TagBadge.vue` | 领涨/领跌等小标签（可选） |
| `dashboard/MarketAiSummary.vue` | AI 主线通栏：**需小改**——把写死的"AI 盘面结论"标签改为可传入（`label` prop），美股页传"今日主线"；改法向后兼容 |
| `composables/useAsyncSection` | 板块/摘要分块异步状态 |
| `utils/format.js` | `formatPercent/formatPrice/formatMv/formatThousands/safeNumber` 等 |

> 为什么不直接复用 `BoardTable / BoardDetailPanel`：字段语义不同（美股板块无"换手率"，成分股无"PE/总市值"常规展示，需"成交额/成交量、涨跌额"与 ticker 表达；且涨跌色与代码前缀策略要单独校验）。复用会引入一坨 `v-if` 分支；新建同风格组件成本更低、隔离性更好。

### 7.3 新建非组件文件

| 文件 | 职责 |
|---|---|
| `frontend/src/api/us.js` | 封装 `getUsSummary / getUsSectors / getUsSectorStocks / getUsAiSummary(SSE)` |
| `frontend/src/composables/useUsMarket.js` | 页面数据编排：summary + sectors + 成分股请求代际 + 轮询/手动刷新 + SSE 摘要；可导出供 UsMarket.vue |
| `frontend/src/composables/useUsCard.js`（或并入 `useDashboardMarket`） | Dashboard 卡片数据（只调 summary） |
| `frontend/src/views/UsMarket.vue` | 见上 |

### 7.4 需改动的现有文件（供落地参考）

- `frontend/src/router/index.js`：加 `/us` 路由（+二期 `/us/stock/:symbol` 注释预留）。
- `frontend/src/components/Layout.vue`：`navBlueprint` 加"美股"，`resolveNavId` 加 `us`。
- `frontend/src/components/app/DesktopSidebar.vue` / `MobileNav.vue`：`isActive` 加 `us` 前缀匹配。
- `frontend/src/views/Dashboard.vue`：在 AI 通栏后插入 `<UsSnapshotCard>`。
- `frontend/src/components/dashboard/MarketAiSummary.vue`：`label` prop 化（可选小改）。

---

## 8. 新增后端 API 端点清单（只给用途与响应形状，不写实现）

建议新增 `backend/app/routes/us.py`，统一前缀 `/api/us`，字段沿用 snake_case。

### 8.1 `GET /api/us/summary` — 美股收盘概览（Dashboard 卡 + 页面摘要区共用一个）

响应形状：

```jsonc
{
  "as_of": "2026-09-02",               // 数据日期（美东交易日）
  "updated_at": "2026-09-03 04:00:00", // 北京时间，用于 UI"xx更新"
  "market_state": "closed",            // open / closed，供 UI 文案
  "indices": [
    { "symbol": "DJI",  "name": "道琼斯",   "value": 34850.2,  "change_amount": 362.4, "change_pct": 1.05 },
    { "symbol": "SPX",  "name": "标普500",   "value": 4512.3,   "change_amount": 32.3,  "change_pct": 0.72 },
    { "symbol": "IXIC", "name": "纳斯达克",  "value": 14032.11, "change_amount": 163.2, "change_pct": 1.18 }
  ],
  "advancers": 3210, "decliners": 4820, "unchanged": 120,   // 可选广度
  "new_highs": 45, "new_lows": 28,                          // 可选，缺省可为 null
  "top_gainers": [ /* UsSector 结构，领涨 Top3 */ ],
  "top_losers":   [ /* UsSector 结构，领跌 Top2-3 */ ]
}
```

### 8.2 `GET /api/us/sectors` — 美股行业板块涨跌全榜

响应：`List<UsSector>`

```jsonc
{
  "name": "半导体",
  "change_pct": 3.42,
  "change_amount": 0,
  "amount": 128.5,                 // 板块成交额（USD，单位随数据层，缺省 0）
  "leading_symbol": "NVDA",        // 领涨 ticker（与 A 股 leading_stock=名称不同，显式拆 ticker+名称）
  "leading_name": "英伟达",
  "leading_change_pct": 4.1,
  "advancers": 32, "decliners": 8, // 内部涨跌家数
  "constituent_count": 48
}
```

### 8.3 `GET /api/us/sectors/{name}/constituents` — 板块成分股（含领涨领跌排序素材）

响应：`List<UsConstituent>`

```jsonc
{
  "symbol": "NVDA", "name": "英伟达",
  "price": 468.3, "change_amount": 18.4, "change_pct": 4.1,
  "volume": 42500000, "amount": 118.2,   // 成交量/成交额（可选）
  "market_cap": 1153000                   // 市值（可选，单位数据层定）
}
```

### 8.4 `GET /api/us/ai-summary` — 美股复盘一句话（SSE，可选）

- 用途：美股页 AI 主线通栏；**不是** Dashboard 卡片的必选项。
- 交互协议照抄 `/api/board/market/ai-summary`：SSE 文本块 + `[DONE]` 收尾；失败首块 `❌` 前缀。
- 依赖：入参为 8.1 + 8.2 的缓存数据；由数据/AI 线负责把"主线板块与领涨股"喂给模型。

> 说明：8.2 是否带 `advancers/decliners/amount` 取决于数据源可用性；前端对缺字段一律走 `--`/隐藏降级（`safeNumber`），不阻塞主流程。全市场"领涨领跌个股榜"本期不做，方案不依赖它；如需页面级"异动股"模块可后续加 `GET /api/us/leaders`。

---

## 9. 两套方案取舍对比

| 维度 | 方案 A：完整板块工作台 | 方案 B：今日主线复盘（极简） |
|---|---|---|
| 页面骨架 | 顶部摘要条 + 常驻"板块榜 | 板块详情"主从工作台 | 指数大卡 + AI 主线 + 领涨/领跌 TopN 双栏 + 抽屉下钻 |
| 信息密度 | 高（全量板块、排序/筛选/分页） | 低（只 Top5 + 一句话叙事） |
| 与 A 股板块页一致性 | 高（同构、可直接迁移心智） | 中（抽屉交互区别于常驻主从） |
| "收盘复盘"任务适配 | 中（能看但偏"浏览工具"） | 高（一屏结论，3 分钟看完） |
| 覆盖全部板块浏览 | 自带 | 需"查看全部"出口（可跳方案 A 形态） |
| 老 A 股用户上手成本 | 极低 | 低（列表更短），但需适应抽屉 |
| 美股新手上手成本 | 中（表多，要会读） | 极低（AI 一句话 + 两块涨跌榜） |
| 移动端体验 | 列表/抽屉（沿用现有） | 纵向堆叠更自然，抽屉下钻轻 |
| 新增组件数 | 少（复用 base 为主） | 与 A 几乎相同 + `compact` 态/抽屉装配 |
| 实现风险 | 低（复刻现成范式） | 低-中（新增桌面抽屉/浮层形态） |
| Dashboard 卡与页面衔接 | 卡 → 全量页 | 卡 → 结论页，衔接最顺 |

**建议**：以**方案 A 为页面骨架**（对齐现有工作台、复用成熟主从范式、支持深链还原），但把顶部"复盘摘要条"升级为方案 B 的叙事元素——3 指数大卡 + 广度 + **AI 今日主线一句话**，让页面既服务"扫一眼结论"也服务"钻取全量"。即"A 的骨架 + B 的摘要带"。若产品更想突出"美股是新的复盘场景、区别于 A 股盘中监控"，则直接选方案 B，实现成本与 A 接近。

---

## 10. 二期 / A 股联动扩展口清单（本期只留位）

1. **美股个股详情**：预留路由 `/us/stock/:symbol`；本期 `UsSectorDetailPanel` 行点击不发跳转（或发占位提示），组件保留 `open-symbol` emit 接口。
2. **A 股联动映射**：`UsSectorDetailPanel` 预留"联动 A 股板块"动作位（按钮/入口隐藏）；页面 query 预留 `?map=A` 语义位，本期不实现。
3. **成分股加入自选**：现有自选 store 是 A 股模型（`code` 数字、分组股票）；美股加入自选需要市场字段，本期不做，行操作位预留。
4. **更多市场**：`/us` 命名空间已把"美股"独立成区，后续港股可对称新增 `/hk`，无需重构导航分组（把导航项分组的逻辑提前留好即可）。
5. **全市场异动榜**：如做"美股当日领涨/领跌个股总榜"，补 `GET /api/us/leaders`，前端可在摘要条或方案 B 中加第三块。

---

## 11. 关键文件路径索引（落地改动点）

- 页面与导航：`frontend/src/views/UsMarket.vue`（新）、`frontend/src/router/index.js`、`frontend/src/components/Layout.vue`、`frontend/src/components/app/DesktopSidebar.vue`、`frontend/src/components/app/MobileNav.vue`
- 新组件：`frontend/src/components/us/*`、`frontend/src/components/dashboard/UsSnapshotCard.vue`
- 复用参照：`frontend/src/views/BoardMonitor.vue`、`frontend/src/components/board/BoardTable.vue`、`frontend/src/components/board/BoardDetailPanel.vue`、`frontend/src/components/dashboard/TopBoards.vue`、`frontend/src/components/dashboard/MarketIndices.vue`、`frontend/src/components/dashboard/MarketAiSummary.vue`
- 数据：`frontend/src/api/us.js`（新）、`frontend/src/composables/useUsMarket.js`（新）、`backend/app/routes/us.py`（新端点，见第 8 节）
- 样式基线：`frontend/src/style.css`（`.workbench-page/__header/toolbar/grid` 全局类）、`frontend/src/styles/tokens.css`
