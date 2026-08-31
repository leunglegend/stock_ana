# 股票详情页 Tab 化改版 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `StockDetail.vue` 从滚动布局重构为 Tab 化布局（行情 / K线 / 财务 / AI分析），并实现 AI 分析自动触发 + 本地缓存机制。

**Architecture:** 仅修改父页面 `StockDetail.vue`，保持 `KLineChart`、`FinancialCard`、`AiAdvice` 三个子组件不动。新增 AI 缓存机制用 localStorage 实现。行情数据从原有 `stockInfo` + `financial` 聚合展示。

**Tech Stack:** Vue 3 + Vite + Element Plus (el-tabs) + Pinia

**Spec:** 阶段二任务3 - 股票详情页 Tab 化改版

## Global Constraints

- 保持所有现有功能完整（K线切换、AI流式输出、财务数据、加自选等）
- KLineChart、FinancialCard、AiAdvice 三个组件尽量不改，只改父页面调用方式
- 项目不在 git 中，直接修改文件
- 使用 CSS 变量（项目已有 tokens.css 设计令牌）
- 中文注释
- 响应式布局
- 构建验证：`cd frontend && npx vite build`

---

## 任务分解

### Task 1: 顶部专业布局 + 面包屑

**Files:**
- Modify: `src/views/StockDetail.vue`

**Interfaces:**
- 消费：`stockInfo`（已存在）、`formatPrice` / `formatChangePct` 等（从 utils/format.js 导入）
- 产出：顶部 header 区域（左侧股票名+代码+加自选按钮，右侧超大价格+涨跌幅+涨跌额）

**Steps:**
- [ ] Step 1: 在 template 中重构 `detail-header` 区域
  - 左侧：返回按钮 + 股票名称（大号 28px 700）+ 代码（小号灰色）+ 加自选主色按钮
  - 右侧：价格（36px+ 加粗 tabular-nums）+ 涨跌幅（20px）+ 涨跌额（16px）
  - 自动染色：涨红跌绿（沿用项目 .text-up / .text-down）
- [ ] Step 2: 添加面包屑（市场概览 / 股票名称），使用 el-breadcrumb
- [ ] Step 3: 优化 CSS，使用 CSS 变量，紧凑高效布局

### Task 2: Tab 导航 + 行情 Tab

**Files:**
- Modify: `src/views/StockDetail.vue`

**Interfaces:**
- 消费：`stockInfo`（open, high, low, close, volume, amount, turnover, pe, pb, total_mv, high_52w, low_52w 等）、`financial`（pe, pb, total_mv, roe 等做补充）
- 产出：el-tabs 组件 + 行情 Tab 内的 4 列网格行情数据

**Steps:**
- [ ] Step 1: 在 header 下方添加 `el-tabs` 组件，4 个 tab-pane（行情 / K线 / 财务 / AI 分析）
- [ ] Step 2: 行情 Tab 中构建 4 列网格布局，每一项 label + value
  - 第一行：今开 / 昨收 / 最高 / 最低
  - 第二行：成交量 / 成交额 / 换手率 / 量比
  - 第三行：PE(TTM) / PB / 总市值 / 流通市值
  - 第四行：52周最高 / 52周最低 / ROE / 毛利率
- [ ] Step 3: 数字使用 tabular-nums，颜色自动染色（最高红/最低绿/PE 亏损绿等）
- [ ] Step 4: 使用 AppCard 组件作为容器，保持风格一致

### Task 3: K线 Tab + 财务 Tab

**Files:**
- Modify: `src/views/StockDetail.vue`

**Interfaces:**
- 消费：`KLineChart` 组件（props: kline-data, loading, @period-change）
- 消费：`FinancialCard` 组件（props: financial, loading）
- 产出：K线 Tab 和 财务 Tab 的内容

**Steps:**
- [ ] Step 1: K线 Tab 中放置 KLineChart 组件，直接复用现有 props 和事件
- [ ] Step 2: 财务 Tab 中放置 FinancialCard 组件，直接复用现有 props
- [ ] Step 3: 确保切换 Tab 时 ECharts 图表正常渲染（el-tab-pane 用 lazy 或手动 resize）

### Task 4: AI 分析 Tab + 自动触发

**Files:**
- Modify: `src/views/StockDetail.vue`

**Interfaces:**
- 消费：`AiAdvice` 组件（props: code, analyzing, advice, @start-analyze）
- 消费：`analyzeStock` API（已存在于 api/stock.js）
- 产出：AI 分析 Tab + 自动触发逻辑 + localStorage 缓存

**Steps:**
- [ ] Step 1: AI 分析 Tab 中放置 AiAdvice 组件
- [ ] Step 2: 新增 `aiCacheKey` 计算属性：`ai_advice_${code}_${YYYY-MM-DD}`
- [ ] Step 3: 新增 `loadAiCache()` 函数，从 localStorage 读取当日缓存
- [ ] Step 4: 新增 `saveAiCache()` 函数，分析完成后写入 localStorage
- [ ] Step 5: 新增 `autoTriggerAi()` 函数，在 K 线和财务数据加载完成后：
  - 检查是否有当日缓存 → 有则直接使用缓存
  - 无缓存 → 自动调用 startAnalyze()
- [ ] Step 6: 在 `loadAllData()` 的 Promise.all 完成后调用 autoTriggerAi()
- [ ] Step 7: watch code 变化时清除旧缓存状态

### Task 5: 构建验证 + 功能检查

**Files:**
- Test: build output

**Steps:**
- [ ] Step 1: 运行 `cd frontend && npx vite build` 确保构建通过
- [ ] Step 2: 检查所有功能点：
  - 4 个 Tab 都能切换
  - K线图正常显示
  - 财务数据正常显示
  - 加自选功能保留
  - 返回按钮正常
  - AI 分析自动触发逻辑完整
