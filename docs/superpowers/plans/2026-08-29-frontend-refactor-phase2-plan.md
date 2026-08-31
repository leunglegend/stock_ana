# 前端重构 · 阶段二：核心页面改版 + AI 驱动范式 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成 4 个核心页面的深度改版，将 AI 从"附加功能"升级为"产品范式"，同时全面应用阶段一建立的设计系统。

**Architecture:** 以阶段一的 Design Token 和基础组件为基础，逐个页面重构。每个页面独立改造，不影响其他页面。后端配合新增批量行情接口和 AI 评分数据结构。

**Tech Stack:** Vue 3 + Vite + Element Plus + ECharts + FastAPI (Python)

**Spec:** 设计 Demo 参考 `.superpowers/brainstorm/13785-1787985101/content/` 目录下的 7 个 demo HTML 文件

**Design Tokens:** 见 `frontend/src/styles/tokens.css`

**Base Components:** 见 `frontend/src/components/base/`（StockName / PriceDisplay / AppCard / TagBadge）

## Global Constraints

- 所有新样式使用 CSS 变量（var(--color-primary-500) 等），不硬编码色值
- 新组件优先使用 base/ 下的基础组件（StockName / PriceDisplay / AppCard / TagBadge）
- 每个页面独立改造，确保其他页面不受影响
- Element Plus 组件样式用 CSS 变量覆盖，不使用 !important
- 中文界面，中文注释
- 保持向后兼容，不删除现有功能
- 后端改动不破坏现有 API 接口（新增接口，不修改已有接口的返回格式）

---

## File Structure

### 前端新增文件
| 文件 | 职责 |
|------|------|
| `frontend/src/components/home/AITodayFocus.vue` | 首页 AI 今日关注模块 |
| `frontend/src/components/watchlist/AIScoreColumn.vue` | 自选股 AI 评分列组件 |
| `frontend/src/components/common/Sparkline.vue` | 迷你走势图（sparkline）组件 |

### 前端修改文件
| 文件 | 修改内容 |
|------|---------|
| `frontend/src/views/Dashboard.vue` | 首页改版：缩小 DateTimeHero + 增加 AI 今日关注 + 优化布局 |
| `frontend/src/views/Watchlist.vue` | 自选股改版：分组 Tab 化 + AI 评分列 + 盈亏总览优化 + 搜索过滤 |
| `frontend/src/views/StockDetail.vue` | 详情页改版：Tab 化布局 + AI 自动触发 + 结构优化 |
| `frontend/src/views/Search.vue` | 搜索页改版：增加行情排行榜 + AI 评分展示 |
| `frontend/src/components/AiAdvice.vue` | AI 分析组件优化：自动触发 + loading 态优化 |

### 后端新增文件
| 文件 | 职责 |
|------|------|
| `frontend/src/api/stock.js` 新增方法 | 批量行情接口调用（前端 API 层） |
| `backend/app/routes/stock.py` 新增接口 | `POST /api/stock/batch-info` 批量行情 |
| `backend/app/services/ai_analyst.py` 扩展 | 增加 AI 评分输出（结构化评级） |

---

## Tasks

### Task 1: 首页改版（砍掉 DateTimeHero + AI 今日关注）

**Files:**
- Create: `frontend/src/components/home/AITodayFocus.vue`
- Create: `frontend/src/components/common/Sparkline.vue`
- Modify: `frontend/src/views/Dashboard.vue`

**Interfaces:**
- Consumes: StockName / PriceDisplay / AppCard / TagBadge 基础组件
- Produces: 新的首页布局，AI 今日关注模块首屏展示

**关键改动：**
1. **缩小 DateTimeHero**：从大横幅改为顶部紧凑信息条（交易状态 + 日期 + 时间），高度从 ~160px 降到 ~60px
2. **新增 AI 今日关注模块**：位于首屏核心位置，展示 2-3 只 AI 精选股票，每只含股票名称、涨跌幅、AI评级徽章、一句话理由
3. **优化三大指数卡片**：更紧凑的横排布局，信息密度提升
4. **市场情绪 + 热门板块布局优化**：保持双栏，但视觉风格统一使用 AppCard
5. **AI 市场点评卡片优化**：视觉风格统一，增加 AI 头像/标识

---

### Task 2: 自选股页面改版

**Files:**
- Modify: `frontend/src/views/Watchlist.vue`
- Modify: `frontend/src/api/stock.js`（新增 batchInfo 方法）
- Modify: `frontend/src/store/index.js`（增加 AI 评分相关字段、自动刷新状态）

**Interfaces:**
- Consumes: StockName / PriceDisplay / TagBadge 组件
- Produces: 改版后的自选股页面 + 批量行情接口调用

**关键改动：**
1. **盈亏总览卡片优化**：收益率更突出（大号数字），增加迷你走势图，总市值/总成本次要展示
2. **分组 Tab 化**：用 Tabs 替代下拉选择器，右侧 "+ 新建分组" 按钮
3. **新增 AI 评分列**：每只股票显示 AI 评级徽章（A+ ~ C）
4. **增加搜索过滤框**：表头上方，可在自选股内搜索过滤
5. **增加列排序**：点击表头可按涨跌幅排序
6. **自动刷新状态**：底部/顶部显示"最后更新时间"和刷新状态指示
7. **批量行情接口**：前端 API 层新增批量获取函数（后端接口在后续任务做，前端先按单只调用的方式保持功能，待后端 ready 后替换）

---

### Task 3: 股票详情页 Tab 化改版

**Files:**
- Modify: `frontend/src/views/StockDetail.vue`
- Modify: `frontend/src/components/AiAdvice.vue`

**Interfaces:**
- Consumes: KLineChart / FinancialCard / AiAdvice / AppCard / PriceDisplay / StockName
- Produces: Tab 化的详情页，AI 分析自动触发

**关键改动：**
1. **Tab 导航**：行情 / K线 / 财务 / AI 分析 四个 Tab，替代滚动布局
2. **顶部专业布局**：左：股票名称 + 代码 + 加自选按钮；右：价格 + 涨跌幅 + 涨跌额（大号专业排版）
3. **行情 Tab**：基本行情数据（开高低收、量额、换手、PE/PB 等）
4. **K线 Tab**：K 线图 + 工具栏（保持原有的 KLineChart 组件）
5. **财务 Tab**：财务指标（保持原有的 FinancialCard 组件，优化展示）
6. **AI 分析 Tab**：进入页面后自动触发 AI 分析（默认选中 K 线 Tab，用户切到 AI 时开始或 onMounted 时后台预加载）
7. **AiAdvice 优化**：自动触发逻辑、loading 态优化、更好的空状态引导

---

### Task 4: 搜索/排行页面改版

**Files:**
- Modify: `frontend/src/views/Search.vue`

**Interfaces:**
- Consumes: StockName / PriceDisplay / TagBadge / AppCard
- Produces: 改版后的搜索排行页面

**关键改动：**
1. **顶部搜索框**：更大更突出的搜索框
2. **行情排行榜 Tab**：涨幅榜 / 跌幅榜 / 成交额榜 / 换手率榜
3. **搜索结果优化**：结果列表中显示 AI 评分列
4. **热门股票**：增加热门股票/板块快捷入口
5. **统一的表格样式**：使用 AppCard 包裹，表头样式统一

---

### Task 5: 后端批量行情接口 + AI 评分结构化

**Files:**
- Modify: `backend/app/routes/stock.py`（新增 POST /batch-info）
- Modify: `backend/app/services/stock_data.py`（新增批量获取函数）
- Modify: `frontend/src/api/stock.js`（前端对接）
- Modify: `frontend/src/views/Watchlist.vue`（切换到批量接口）

**Interfaces:**
- Produces: `POST /api/stock/batch-info` 批量行情接口

**关键改动：**
1. **后端新增批量接口**：接受股票代码数组，一次返回全部行情
2. **AI 评分字段**：在个股/批量行情中可返回 AI 评级（可选参数）
3. **前端对接**：自选股页面切换到批量接口，提升加载速度
4. **性能验证**：10 只股票从串行 5-10 秒降到 < 2 秒

---

### Task 6: 阶段二回归验证

**Files:** 所有页面

**Interfaces:**
- 验证所有改动不破坏现有功能

**关键检查：**
1. 构建验证：`npm run build` 通过
2. 首页：AI 今日关注展示正常，三大指数正常
3. 自选股：分组 Tab 正常，列表正常，加自选正常
4. 详情页：Tab 切换正常，K 线正常，AI 分析正常
5. 搜索页：搜索功能正常，排行榜展示正常
6. 其他页面（板块/复盘）：未受影响
7. 后端批量接口：调用正常，数据正确
8. 路由跳转：所有导航正常

---

**阶段二交付物：**
1. ✅ 首页改版（AI 今日关注 + 紧凑信息条 + 优化布局）
2. ✅ 自选股改版（分组 Tab + AI 评分 + 排序筛选 + 盈亏优化）
3. ✅ 详情页改版（Tab 化布局 + AI 自动分析）
4. ✅ 搜索排行页改版（多榜 Tab + AI 评分）
5. ✅ 后端批量行情接口
6. ✅ 构建通过，功能完整可用
