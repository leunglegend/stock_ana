# Balanced Workbench Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将前端主要页面统一为已确认的 A 方案“均衡研究台”，保持现有业务行为与接口不变。

**Architecture:** 在 `style.css` 建立共享页面骨架、页头与双栏布局契约，各视图只保留自身比例和响应式顺序。页面组件继续负责现有数据与交互，排版改动限定在模板外层和样式层。

**Tech Stack:** Vue 3、Vite、Element Plus、CSS Grid、Node.js test runner

---

### Task 1: 建立共享布局契约

**Files:**
- Create: `frontend/tests/layout-contract.test.js`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/components/Layout.vue`

- [ ] **Step 1: 写入失败的源码契约测试**

新增测试读取全局样式和七个视图源码，断言存在 `.workbench-page`、`.workbench-page__header`、`.workbench-grid`、`.workbench-grid--primary`，并断言统一断点 `1023px` 与移动断点 `767px`。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && node --test tests/layout-contract.test.js`

Expected: FAIL，提示全局样式缺少工作台布局类。

- [ ] **Step 3: 实现共享骨架**

在 `style.css` 增加共享页面最大宽度、间距、紧凑页头、50/50 与 60/40 网格；在 `Layout.vue` 收紧桌面和平板内容留白，并保证移动端底部导航安全区不变。

- [ ] **Step 4: 运行契约测试**

Run: `cd frontend && node --test tests/layout-contract.test.js`

Expected: PASS。

### Task 2: 重构市场概览与板块发现

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/BoardMonitor.vue`
- Modify: `frontend/src/components/board/BoardDetailPanel.vue`

- [ ] **Step 1: 应用市场概览统一骨架**

为页面根节点、页头与两组双栏接入共享类；指数保持首要信息带，两组模块复用同一列轨；删除与共享规则重复的局部 CSS。

- [ ] **Step 2: 应用板块主次工作区**

将 Tab 和筛选器合并为紧凑工具区；桌面端列表与详情使用 60/40 布局，平板和移动端保持现有抽屉/面板行为。

板块列表和成分股在过滤、排序后执行客户端分页，每页 10 条；筛选、Tab 切换或打开新板块时回到第 1 页。

- [ ] **Step 3: 运行契约测试与构建**

Run: `cd frontend && node --test tests/layout-contract.test.js && npm run build`

Expected: 测试通过，Vite 构建退出码为 0。

### Task 3: 重构自选、个股与搜索页面

**Files:**
- Modify: `frontend/src/views/Watchlist.vue`
- Modify: `frontend/src/views/StockDetail.vue`
- Modify: `frontend/src/views/Search.vue`

- [ ] **Step 1: 收紧自选页层级**

将页头、分组 Tab、筛选工具和主列表依次接入共享垂直节奏；移动端主要操作保持整行触控尺寸。

自选列表在筛选和排序后执行客户端分页，每页 10 条；切换分组或筛选排序后回到第 1 页。

- [ ] **Step 2: 稳定个股详情锚点**

统一股票身份区、行情事实网格和 Tab 内容宽度；为 Tab 内容设置稳定最小高度，避免切换时明显跳动。

- [ ] **Step 3: 合并搜索上下文与输入区**

将标题、最近搜索和输入工具组成首要信息区；结果列表保持主任务优先，移动端输入与按钮纵向排列。

搜索结果执行客户端分页，每页 10 条；新搜索和关键词变化后回到第 1 页。

- [ ] **Step 4: 运行契约测试与构建**

Run: `cd frontend && node --test tests/layout-contract.test.js && npm run build`

Expected: 测试通过，Vite 构建退出码为 0。

### Task 4: 重构报告列表与阅读器

**Files:**
- Modify: `frontend/src/views/Reports.vue`
- Modify: `frontend/src/views/ReportDetail.vue`

- [ ] **Step 1: 展开并整理压缩源码**

仅格式化两个视图的模板、脚本与样式，使后续排版修改可审查；不得改变请求、轮询和报告解析逻辑。

- [ ] **Step 2: 应用报告列表骨架**

将生成按钮、轮询状态和列表组合为稳定纵向工作区；分页与状态反馈保持固定位置。

- [ ] **Step 3: 应用 70/30 阅读布局**

桌面端目录与正文使用约 30/70 双栏；平板以下降为单栏，目录在正文之前，正文保留可读行宽与代码块横向滚动。

- [ ] **Step 4: 运行契约测试与构建**

Run: `cd frontend && node --test tests/layout-contract.test.js && npm run build`

Expected: 测试通过，Vite 构建退出码为 0。

### Task 5: 全量验证与视觉验收

**Files:**
- Modify when required by findings: `frontend/src/style.css`
- Modify when required by findings: `frontend/src/views/*.vue`

- [ ] **Step 1: 运行全部现有测试**

Run: `cd frontend && node --test tests/*.test.js`

Expected: 所有 Node 测试通过。

- [ ] **Step 2: 运行生产构建**

Run: `cd frontend && npm run build`

Expected: Vite 构建成功且无编译错误。

- [ ] **Step 3: 启动开发服务器**

Run: `cd frontend && npm run dev -- --host 0.0.0.0 --port 52766`

Expected: 页面可通过 `http://localhost:52766` 访问；`52765` 继续保留给视觉伴侣。

- [ ] **Step 4: 检查四档视口**

在 `1440x900`、`768x1024`、`390x844`、`360x800` 检查市场、板块、自选、个股、搜索、报告列表和报告详情。验证无非预期横向滚动、遮挡、文本溢出、布局跳动或卡片嵌套。

- [ ] **Step 5: 检查关键路径与控制台**

验证搜索进入个股、板块打开详情、自选操作入口、报告列表进入详情；确认控制台没有本次改动引入的新错误。

- [ ] **Step 6: 检查工作区差异**

Run: `git diff --check && git status --short`

Expected: 无空白错误；只汇报本次相关改动，不覆盖或回退用户已有变更。

> 提交步骤未写入计划：当前项目规则要求 Git 历史操作必须先获得用户确认。
