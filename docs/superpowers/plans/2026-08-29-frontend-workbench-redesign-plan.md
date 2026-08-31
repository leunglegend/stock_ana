# 股票分析前端工作台完全重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不修改后端 API、数据库 schema 或依赖的前提下，将现有前端重构为专业、响应式、可访问且只展示真实数据的 A 股研究工作台。

**Architecture:** 先串行建立设计系统、通用组件、鉴权续航和响应式应用外壳，再按页面所有权并行重构市场研究页与用户数据页。SQLite 继续作为用户资料及登录后业务数据的唯一事实来源；前端通过现有 API 读取，不持久化 `userInfo`。

**Tech Stack:** Vue 3、Vite、Vue Router、Pinia、Element Plus、ECharts、Axios、Marked、SQLite（现有后端）

**Spec:** `docs/superpowers/specs/2026-08-29-frontend-workbench-redesign.md`

---

## 执行边界

- 不修改 `backend/`、`frontend/package.json` 或 `frontend/package-lock.json`。
- 不新增排行榜、批量行情、AI 推荐、持仓股数或历史报告重试能力。
- 所有业务字段必须能映射到现有 API schema 或规格中的明确公式。
- `Layout.vue`、`router/index.js`、`style.css`、`tokens.css`、两个 Store 由总控串行修改。
- 页面并行任务不得修改共享文件；需要共享能力时停止并交由总控整合。
- 未获明确授权前不执行 `git commit`、merge、rebase、push。

## 目标文件结构

```text
frontend/src/
├── components/
│   ├── app/             # AppShell 子组件：Sidebar、CommandBar、MobileNav
│   ├── base/            # SectionPanel、StatusState、StockIdentity、PriceDisplay
│   ├── dashboard/       # 首页指标、宽度、板块、自选与 AI 点评
│   ├── stock/           # 个股头部与详情 Tabs
│   ├── watchlist/       # 分组栏、过滤栏、桌面表格、移动列表
│   └── reports/         # 报告列表行、详情目录、正文段落
├── composables/
│   ├── useConcurrentRequests.js
│   ├── useAsyncSection.js
│   └── useResponsive.js
├── utils/
│   ├── format.js
│   └── markdown.js
├── styles/
│   └── tokens.css
└── views/               # 只负责页面编排和数据协调
```

## 阶段一：基础层（串行）

### Task 1: 建立语义设计系统

**Files:**
- Modify: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/components/base/AppCard.vue`
- Modify: `frontend/src/components/base/PriceDisplay.vue`
- Modify: `frontend/src/components/base/StockName.vue`
- Modify: `frontend/src/components/base/TagBadge.vue`

- [ ] **Step 1: 将 `tokens.css` 接入全局样式并改为规格中的中性工作台色系**

  在 `style.css` 首行加入 `@import './styles/tokens.css';`。补齐 `--surface-*`、`--text-*`、`--border-*`、`--focus-ring`、`--z-*` 和图表 Token；保留旧变量别名，避免未迁移页面瞬间失效。

- [ ] **Step 2: 建立全局基础规则**

  在 `style.css` 定义 `box-sizing`、body、`.tabular-nums`、`.text-up/.text-down`、`:focus-visible`、`prefers-reduced-motion`、稳定滚动条和 `#app` 最小高度。禁止全局移除 outline。

- [ ] **Step 3: 修正基础组件契约**

  `AppCard` 默认 `hoverEffect=false`、`shadow=false`；`PriceDisplay` 接受 `null` 并显示 `--`，平盘使用中性色；`TagBadge` 改为小圆角而非胶囊；`StockName` 在窄容器允许换行。

- [ ] **Step 4: 构建验证**

  Run: `cd frontend && npm run build`

  Expected: exit code `0`，无 CSS import 或 Vue 编译错误。

### Task 2: 增加通用状态与请求协调能力

**Files:**
- Create: `frontend/src/components/base/SectionPanel.vue`
- Create: `frontend/src/components/base/StatusState.vue`
- Create: `frontend/src/components/base/MetricCell.vue`
- Create: `frontend/src/composables/useConcurrentRequests.js`
- Create: `frontend/src/composables/useAsyncSection.js`
- Modify: `frontend/src/utils/format.js`

- [ ] **Step 1: 创建稳定尺寸的面板和状态组件**

  `SectionPanel` 只提供 header/default/footer 插槽；`StatusState` 支持 `loading/empty/error`、`retry` 事件和 `aria-live`；`MetricCell` 统一标签、数值、单位和涨跌语义。

- [ ] **Step 2: 创建并发上限为 4 的逐项请求器**

  `runWithConcurrency(items, worker, limit = 4, onSettled)` 必须保持输入顺序，单项失败返回 `{ status: 'rejected', reason }`，不让整个批次 reject。

- [ ] **Step 3: 统一空值格式化**

  调整 `formatVolume/formatAmount`：`null/undefined` 返回 `--`，合法数字 `0` 返回 `0`；增加 `safeNumber`、`formatFetchTime` 和 `calculateRiseRatio`，后者分母为 0 时返回 `null`。

- [ ] **Step 4: 使用 Node 内置断言定向验证纯函数**

  Run: `cd frontend && node --input-type=module -e "import('./src/utils/format.js').then(m => { console.assert(m.calculateRiseRatio(0,0,0) === null); console.assert(m.calculateRiseRatio(3,1,0) === 75); console.assert(m.formatAmount(0) === '0'); })"`

  Expected: exit code `0`，无 assertion 输出。

### Task 3: 将用户资料事实来源收敛到 SQLite

**Files:**
- Modify: `frontend/src/store/user.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/api/http.js`
- Modify: `frontend/src/components/LoginModal.vue`

- [ ] **Step 1: 移除 `stock_user_info` 的 localStorage 持久化**

  Store 仅从 `stock_user_token` 恢复令牌；`userInfo` 初始为 `null`；`fetchUserInfo()` 通过 `/auth/me` 写入内存。增加 `authReady` 和 `initializeAuth()`，确保只初始化一次。

- [ ] **Step 2: 增加目标路由续航**

  路由守卫统一读取 `meta.requiresAuth`；未登录时保存 `to.fullPath` 到内存态 `pendingRoute`，弹登录框并取消当前导航。`/watchlist` 明确设置 `requiresAuth: true`。

- [ ] **Step 3: 处理登录成功和 401**

  `LoginModal` 登录成功后读取并清空 `pendingRoute`，然后 `router.push(target)`。401 保存当前路由、清理令牌和内存用户，再弹登录框；同一批 401 只触发一次。

- [ ] **Step 4: 验证浏览器持久化边界**

  启动后检查 localStorage 只允许存在令牌和未登录自选数据，不存在 `stock_user_info`；刷新页面后 `/auth/me` 成功恢复用户名。

### Task 4: 重构全局外壳和搜索对话框

**Files:**
- Modify: `frontend/src/components/Layout.vue`
- Modify: `frontend/src/components/GlobalSearch.vue`
- Modify: `frontend/src/router/index.js`
- Create: `frontend/src/components/app/DesktopSidebar.vue`
- Create: `frontend/src/components/app/CommandBar.vue`
- Create: `frontend/src/components/app/MobileNav.vue`
- Create: `frontend/src/composables/useResponsive.js`

- [ ] **Step 1: 拆分应用外壳**

  桌面侧栏只显示市场、板块、自选、复盘；搜索从一级导航移除。`CommandBar` 承载全局搜索、通知和用户菜单；`MobileNav` 在 `<768px` 显示四个带文字标签的入口。

- [ ] **Step 2: 修复全局搜索可访问性**

  使用 `role="dialog"`、`aria-modal="true"`、语义按钮/列表项、方向键、Enter、Escape、焦点陷阱和关闭后焦点归还。删除 `outline:none`，保留现有 `/` 与 `Ctrl/Cmd+K`。

- [ ] **Step 3: 增加路由上下文和主标题焦点**

  路由切换后将焦点移动到 `[data-page-title]`；个股详情和报告详情保持 hidden；搜索页保留路由但不显示在主导航。

- [ ] **Step 4: 构建并进行壳层 smoke check**

  Run: `cd frontend && npm run build`

  Expected: exit code `0`。在 `360x800` 与 `1440x900` 下分别确认底部导航和固定侧栏，不出现双导航或内容遮挡。

## 阶段二：市场研究页（基础层完成后可并行）

### Task 5: 市场概览首页

**Ownership:** 仅修改以下文件，不修改共享 Store、路由和全局样式。

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`
- Remove usage: `frontend/src/components/DateTimeHero.vue`
- Create: `frontend/src/components/dashboard/MarketIndices.vue`
- Create: `frontend/src/components/dashboard/MarketBreadth.vue`
- Create: `frontend/src/components/dashboard/TopBoards.vue`
- Create: `frontend/src/components/dashboard/WatchlistSnapshot.vue`
- Create: `frontend/src/components/dashboard/MarketAiSummary.vue`

- [ ] **Step 1: 删除大 Hero，建立真实数据首屏**

  用 `getMarketSummary()` 驱动指数、成交额和涨跌分布；上涨占比仅通过 `calculateRiseRatio` 派生。

- [ ] **Step 2: 绑定板块和自选数据**

  `TopBoards` 只消费 `BoardInfo` 字段；`WatchlistSnapshot` 最多取 5 只并使用并发限制 4，未登录显示登录动作，单项失败显示行级重试。

- [ ] **Step 3: 独立处理 AI SSE**

  AI 点评按需生成；重新生成前关闭旧连接；离开页面关闭连接；失败只影响 AI 面板。

- [ ] **Step 4: 构建验证**

  Run: `cd frontend && npm run build`

  Expected: exit code `0`；源码中不出现分时序列、放量、新高或交易日历字段。

### Task 6: 搜索页

**Files:**
- Modify: `frontend/src/views/Search.vue`
- Create: `frontend/src/components/stock/SearchResults.vue`
- Create: `frontend/src/components/watchlist/GroupPicker.vue`

- [ ] **Step 1: 搜索命中与行情加载解耦**

  `searchStock()` 返回后立即渲染 `code/name`；前 20 条通过并发限制 4 逐行补充 `StockInfo`，新搜索开始时忽略旧请求结果。

- [ ] **Step 2: 删除硬编码热门股票**

  最近搜索只写入独立 localStorage key，最多 8 条并提供清除；空状态不展示推荐股票。

- [ ] **Step 3: 加自选时选择分组**

  `GroupPicker` 显示真实分组；成功反馈包含分组名称；未登录时进入登录续航流程。

- [ ] **Step 4: 验证搜索状态**

  覆盖未搜索、搜索中、无命中、部分行情失败、快速连续输入和进入详情六种状态；运行 `npm run build`。

### Task 7: 板块发现页

**Files:**
- Modify: `frontend/src/views/BoardMonitor.vue`
- Create: `frontend/src/components/board/BoardTable.vue`
- Create: `frontend/src/components/board/BoardDetailPanel.vue`

- [ ] **Step 1: 将卡片网格改为可扫描表格**

  行业/概念 Tab 懒加载；筛选和排序只使用 `BoardInfo` 的现有字段，0 与缺失值分开显示。

- [ ] **Step 2: 修复首页深链接**

  读取 `route.query.name/type`，切换正确 Tab 并打开对应板块。关闭面板时清理 query；返回首页后保持先前滚动位置。

- [ ] **Step 3: 重构成分股详情**

  桌面使用侧栏，移动端全屏；只展示 `BoardStock` 字段。使用列表接口返回的板块涨跌幅，不再对成分股求平均伪造板块涨幅。

- [ ] **Step 4: 验证**

  运行 `npm run build`，并验证行业、概念、深链接、空列表、503 和移动全屏面板。

### Task 8: 个股详情页

**Files:**
- Modify: `frontend/src/views/StockDetail.vue`
- Modify: `frontend/src/components/KLineChart.vue`
- Modify: `frontend/src/components/FinancialCard.vue`
- Modify: `frontend/src/components/AiAdvice.vue`
- Create: `frontend/src/components/stock/StockHeader.vue`
- Create: `frontend/src/components/stock/QuoteFacts.vue`

- [ ] **Step 1: 建立四 Tab 工作台**

  固定股票头部和报价事实栏；行情、K 线、财务、AI 各自使用独立加载/空/错状态。默认打开 K 线 Tab。

- [ ] **Step 2: 保留真实 K 线能力并统一图表 Token**

  日/周/月 K 与成交量、MACD、KDJ、RSI 均绑定现有字段；ECharts 颜色从 CSS Token 读取；图表容器使用稳定高度。

- [ ] **Step 3: 收敛财务和 AI 展示**

  财务只显示 schema 字段，`null` 显示 `--`。AI 由用户主动触发，评分 JSON 可选，失败退化为正文；离开页面关闭 SSE。

- [ ] **Step 4: 验证**

  运行 `npm run build`；检查每个 Tab 独立失败、周期切换、指标切换、无财务数据和 AI 未配置。

## 阶段三：用户数据页（共享 Store 收尾后可并行）

### Task 9: 完成自选 Store 能力并重构“我的自选”页

**Files:**
- Modify: `frontend/src/store/index.js`（总控先完成 Store 方法）
- Modify: `frontend/src/views/Watchlist.vue`
- Create: `frontend/src/components/watchlist/GroupTabs.vue`
- Create: `frontend/src/components/watchlist/WatchlistTable.vue`
- Create: `frontend/src/components/watchlist/WatchlistMobileList.vue`
- Create: `frontend/src/components/watchlist/WatchlistFilters.vue`

- [ ] **Step 1: 总控补齐 Store 方法**

  增加 `renameGroup(groupId, name)`、`addStockToGroup(groupId, stock)`、`updateStock(code, { cost, remark })`。云端调用现有 API，本地模式更新 localStorage；方法返回明确成功/失败结果。

- [ ] **Step 2: 删除所有固定股数和组合汇总**

  移除 `shares: 100`、总市值、总成本、总盈亏。只在成本大于 0 且行情存在时计算每股盈亏与成本收益率。

- [ ] **Step 3: 重构分组、过滤和行级行情状态**

  分组改 Tab；启用真实重命名；增加筛选、排序和更新时间。行情并发上限 4，每行独立重试。

- [ ] **Step 4: 建立移动摘要列表**

  `<768px` 隐藏宽表，显示名称/代码、价格、涨跌幅、成本摘要；编辑操作进入底部面板。

- [ ] **Step 5: 验证**

  运行 `npm run build`；检查分组增改删、成本为 0、备注、单股失败、本地/SQLite 云端切换和移动端操作。

### Task 10: 安全 Markdown 与复盘页

**Files:**
- Create: `frontend/src/utils/markdown.js`
- Modify: `frontend/src/views/Reports.vue`
- Modify: `frontend/src/views/ReportDetail.vue`
- Create: `frontend/src/components/reports/ReportTable.vue`
- Create: `frontend/src/components/reports/ReportOutline.vue`

- [ ] **Step 1: 创建安全 Markdown 渲染器**

  使用现有 Marked 自定义 renderer：原始 HTML token 转义为文本；链接仅允许 `http/https`；渲染后移除事件属性和危险 URL。导出 `renderSafeMarkdown(text)`，页面不直接调用 `marked.parse()`。

- [ ] **Step 2: 将报告卡片改为紧凑列表**

  展示日期、真实状态、股票数、摘要和时间；只有 `completed` 可打开详情；历史失败行不显示重新生成。

- [ ] **Step 3: 实现真实状态轮询**

  生成今日报告后每 5 秒按 `report_id` 查询，完成/失败/离页/2 分钟时停止，超时保留手动刷新。

- [ ] **Step 4: 重构报告阅读器**

  使用目录 + 正文布局展示市场总览、关注重点、个股分析和风险；评分解析失败时隐藏徽章；所有 Markdown 使用安全渲染器。

- [ ] **Step 5: 验证**

  运行 `npm run build`；检查四种状态、空报告、分页、轮询停止、恶意 HTML 文本转义和移动端目录。

### Task 11: 通知与登录可访问性

**Files:**
- Modify: `frontend/src/components/NotificationBell.vue`
- Modify: `frontend/src/components/LoginModal.vue`

- [ ] **Step 1: 语义化通知交互**

  铃铛使用 button，通知项使用 button/link；支持 Enter/Space，未读状态包含文字；操作结果通过 `aria-live` 通知。

- [ ] **Step 2: 保持真实通知状态**

  登录后每 60 秒查询未读数；打开列表再拉取通知；标记已读成功后才更新本地数值；`type=report && ref_id` 才跳详情。

- [ ] **Step 3: 完善登录焦点和错误恢复**

  打开对话框聚焦用户名；验证错误聚焦首个无效字段；关闭后焦点归还触发器；成功后执行 Task 3 的目标路由续航。

- [ ] **Step 4: 验证**

  纯键盘完成打开通知、标记已读、打开报告、登录和关闭对话框；运行 `npm run build`。

## 阶段四：统一收尾

### Task 12: 清理旧样式和整合冲突

**Files:**
- Modify: all touched frontend files only as needed
- Remove only after usage scan: `frontend/src/components/DateTimeHero.vue`, `frontend/src/components/HelloWorld.vue`

- [ ] **Step 1: 枚举旧组件引用**

  Run: `cd frontend && rg -n "DateTimeHero|HelloWorld|card-shadow|linear-gradient|!important" src`

  Expected: 已迁移页面无旧 Hero、装饰渐变或补丁式 `!important`；确认零引用后再申请删除文件，未经确认不删除。

- [ ] **Step 2: 扫描业务数据越界**

  Run: `cd frontend && rg -n "shares:\s*100|AI 今日关注|涨幅榜|跌幅榜|成交额榜|52周|量比|流通市值" src`

  Expected: 无命中。

- [ ] **Step 3: 扫描前端用户资料持久化**

  Run: `cd frontend && rg -n "stock_user_info|USER_KEY|localStorage.*userInfo" src`

  Expected: 无命中；用户资料只由 `/auth/me` 写入 Pinia 内存。

### Task 13: 最终验证

**Files:**
- No source changes unless verification exposes an in-scope defect

- [ ] **Step 1: 生产构建**

  Run: `cd frontend && npm run build`

  Expected: exit code `0`。

- [ ] **Step 2: 启动前后端并检查接口**

  使用仓库文档命令启动 FastAPI 与 Vite。验证市场、板块、股票、K 线、财务、认证、自选、报告和通知请求无新增 4xx/5xx。

- [ ] **Step 3: Playwright 跨视口验证**

  使用已安装的 `/home/miniconda3/bin/playwright`，在 `360x800`、`390x844`、`768x1024`、`1440x900` 截图首页、搜索、自选、板块、详情、报告。检查非空、无横向滚动、无遮挡、控制台无错误。

- [ ] **Step 4: 关键路径 smoke test**

  依次验证搜索到详情并加自选、首页到板块到个股、未登录访问受保护页后登录回跳、通知到报告、今日报告真实状态刷新。

- [ ] **Step 5: 无障碍检查**

  纯键盘完成四条关键路径；检查对话框焦点陷阱、可见焦点、44px 触点、`aria-live` 和 reduced-motion。

- [ ] **Step 6: 汇总交付**

  报告改动、验证命令与结果、剩余风险、未实现的后端能力。未经明确授权不提交、推送或删除文件。

## 并行调度建议

1. 总控串行完成 Task 1-4。
2. Task 5-8 分配四个只读共享、独占写入范围的 Agent 并行执行。
3. 总控先完成 Task 9 Step 1，再并行执行 Task 9 页面部分、Task 10、Task 11。
4. 所有 Agent 返回后由总控执行 Task 12-13，检查共享组件兼容、路由上下文和视觉一致性。

每个并行 Agent 必须只修改任务列出的文件；发现需要改共享文件、API、schema、依赖或锁文件时立即停止并上报。
