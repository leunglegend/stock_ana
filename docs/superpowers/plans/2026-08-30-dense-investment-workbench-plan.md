# Institutional Investment Workbench v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 严格映射已确认的视觉伴侣 v1，将八个用户页面重构为连续、紧凑、适合投资决策扫描的浅色研究工作台，同时保留现有业务行为并补齐缺失的可达操作。

**Architecture:** 六个实现域并发写入互不重叠的页面和测试文件；共享 Token、Element Plus 适配、Shell 与基础面板只由 Shell Agent 修改。主 Agent 不把子任务完成视作整合完成，统一处理共享入口、功能缺口、视觉回归和全量验证。

**Tech Stack:** Vue 3、Vite、Element Plus、Pinia、ECharts、CSS Grid、Node.js test runner

---

### Task 1: 建立共享视觉契约

**Files:**
- Modify: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/style.css`
- Create: `frontend/src/styles/element-plus.css`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/components/base/SectionPanel.vue`
- Modify: `frontend/tests/new-feature-style-contract.test.js`
- Modify: `frontend/tests/layout-contract.test.js`

- [ ] 在契约测试中断言 `--radius-pill`、数据行/控件/导航密度 Token、Element Plus 统一适配文件和四档断点存在。
- [ ] 运行 `cd frontend && node --test tests/new-feature-style-contract.test.js tests/layout-contract.test.js`，确认新断言先失败。
- [ ] 收敛颜色、表面、边界、圆角、阴影和密度 Token；普通面板取消阴影并支持 `standard/flush/overlay`。
- [ ] 在 `element-plus.css` 统一按钮、输入、表格、Tabs、分页、抽屉和弹层的视觉尺寸与状态。
- [ ] 运行定向测试和 `npm run build`，冻结共享层后页面 Agent 不再修改上述文件。

### Task 2: 重构应用壳层与唯一浅色研究主题

**Ownership:** `frontend/src/components/Layout.vue`、`frontend/src/components/app/*`、`frontend/src/components/GlobalSearch.vue`

- [ ] 将 CommandBar 改为连续工具栏，去除卡片圆角、模糊和常规阴影。
- [ ] 实现 `>=1280` 完整侧栏、`1024-1279` 图标轨道、`768-1023` 顶栏抽屉、`<768` 顶栏加底部导航。
- [ ] 手机首行只保留菜单、搜索、通知等高频入口，主题和账户降低层级。
- [ ] 桌面侧栏固定 `168px`；隐藏主题换肤入口，但保留底层兼容，避免影响已有状态或图表监听。
- [ ] 运行壳层契约测试与生产构建并自审；不得改共享 Token、基础组件或其他页面。

### Task 3: 重构市场概览

**Ownership:** `frontend/src/views/Dashboard.vue`、`frontend/src/components/dashboard/*`、`frontend/tests/institutional-dashboard-contract.test.js`

- [ ] Dashboard 按交易状态、市场脉冲、板块强弱、自选待处理、AI 次级摘要重排。
- [ ] 把指数、板块和自选快照从行卡改为连续指标带/分隔列表，删除英文 eyebrow 和重复说明。
- [ ] 主工作区严格按 `2:1` 展示板块表与自选待处理检查器，AI 摘要为底部单行带。
- [ ] 运行市场契约测试、相关测试和构建并自审。

### Task 4: 重构板块发现与机会雷达

**Ownership:** `frontend/src/views/BoardMonitor.vue`、`frontend/src/views/OpportunityRadar.vue`、`frontend/src/components/board/*`、`frontend/src/components/radar/*`、`frontend/tests/institutional-discovery-contract.test.js`

- [ ] 先写契约测试并验证失败，再实现 `58:42` 板块主从面和 `30:70` 雷达候选面。
- [ ] BoardMonitor 将筛选、总数和分页并入工具栏，右侧事实带和成分股表组成连续检查器。
- [ ] OpportunityRadar 增加四格结果摘要，左侧只保留板块信号索引，右侧候选表固定操作列。
- [ ] 保留已有深链竞态修复、分页、请求状态和加入自选；平板/移动详情不得落到主列表下形成长滚动。
- [ ] 运行发现域契约测试、相关测试和构建并自审。

### Task 5: 重构自选研究队列

**Ownership:** `frontend/src/views/Watchlist.vue`、`frontend/src/components/watchlist/*`、`frontend/src/components/StockSearch.vue`、`frontend/tests/institutional-watchlist-contract.test.js`

- [ ] 将分组、总数、刷新、添加、筛选和排序收敛到紧凑工具区。
- [ ] 信号中心默认只显示摘要和前三条；主表成为首要工作区，信号改为表内状态或精简摘要。
- [ ] 桌面使用约 `40px` 连续数据行；平板只显示核心五列；移动使用 `68-76px` 单行标的和更多菜单。
- [ ] 保留分页、分组、编辑、删除和持久化行为，切换筛选后页码复位。
- [ ] 运行自选相关测试、全部前端测试和构建并自审。

### Task 6: 重构个股研究页

**Ownership:** `frontend/src/views/StockDetail.vue`、`frontend/src/components/stock/*`、`frontend/src/components/KLineChart.vue`、`frontend/src/components/FinancialCard.vue`、`frontend/src/components/AiAdvice.vue`、`frontend/tests/institutional-stock-contract.test.js`

- [ ] 个股页只保留一份行情事实，扩大 K 线主区，技术/财务/AI 作为二级研究区。
- [ ] 顶部身份价格带与 `72:28` 图表/检查器比例严格映射视觉稿，删除重复行情事实。
- [ ] 删除模板中的英文 eyebrow、教学说明和无功能价值的表面层，不改请求、流式分析和轮询逻辑。
- [ ] 运行个股契约测试、相关测试和构建并自审。

### Task 7: 重构搜索与报告

**Ownership:** `frontend/src/views/Search.vue`、`frontend/src/views/Reports.vue`、`frontend/src/views/ReportDetail.vue`、`frontend/src/components/stock/SearchResults.vue`、`frontend/src/components/reports/*`、`frontend/src/utils/markdown.js`、`frontend/tests/institutional-research-contract.test.js`

- [ ] 先写契约测试并验证失败，再实现搜索工具带、结果控制带、报告连续表和报告阅读列。
- [ ] 搜索分页保持桌面完整、移动简化；最近搜索只作为标题带辅助信息。
- [ ] 报告列表强化日期、结论、风险、重点股票和完成时间；详情先结论、风险、关联股票，再进入 `60-68ch` 正文。
- [ ] 保留搜索、自选添加、报告生成、轮询、错误和 Markdown 安全行为。
- [ ] 运行研究域契约测试、相关测试和构建并自审。

### Task 8: 新功能盘点与整合

**Files:**
- Read: `frontend/src/router/index.js`
- Read: `frontend/src/views/*`
- Read: `frontend/src/components/*`
- Modify only when findings require: corresponding frontend view/component files

- [ ] 对比路由、视图、组件和现有计划，识别本轮并行期间新增的用户可见功能。
- [ ] 对新增功能逐一套用 Page/Toolbar/Panel/DataRow 视觉契约，不修改业务 contract。
- [ ] 扫描未定义 CSS 变量、常规 `el-card`、英文 eyebrow、重复标题和页面原始颜色；修复本轮范围内问题。

### Task 9: 统一验收与双阶段审查

- [ ] 运行 `cd frontend && node --test tests/*.test.js`。
- [ ] 运行 `cd frontend && npm run build`。
- [ ] 运行 `git diff --check`，检查并行改动是否有同文件冲突或共享层越权。
- [ ] 通过 `http://localhost:52764` 检查主要路由返回和静态资源。
- [ ] 在 `1440x900`、`1024x768`、`390x844`、`360x800` 检查横向溢出、遮挡、卡片嵌套、首屏密度和移动操作。
- [ ] 由规格审查 Agent 对照设计逐项检查，再由代码质量 Agent 检查回归风险；重要问题修复后重新验证。

> 当前工作区位于 `main` 且已有大量未提交改动。用户已明确授权在当前工作区继续开发，但未授权任何 Git 历史或远程操作，因此本计划不包含 commit、push、merge、rebase 或文件删除。
