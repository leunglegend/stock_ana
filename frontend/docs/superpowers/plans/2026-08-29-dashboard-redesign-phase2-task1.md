# 首页（市场概览）改版 实现计划 — 阶段二任务 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 Dashboard 首页，将 AI 驱动元素放到首屏核心位置，统一使用 AppCard 设计系统，缩小 DateTimeHero 为顶部紧凑信息条。

**Architecture:** 单页面重构，主文件 `views/Dashboard.vue`，配合 `components/DateTimeHero.vue` 新增 compact prop。所有卡片使用 `AppCard` 组件统一视觉风格。AI 今日关注模块使用模拟数据（3只股票），点击跳转股票详情页。

**Tech Stack:** Vue 3 (Composition API / `<script setup>`), Element Plus, CSS Variables (设计令牌系统 `styles/tokens.css`)

**Spec:** 任务说明文档 — 见用户输入的 5 项具体改动

## Global Constraints

- 不删除任何现有功能（DateTimeHero 只是紧凑化，不是删除）
- AI 今日关注的股票点击跳转到 `/stock/:code`
- 保持响应式布局（`el-row/el-col` 体系）
- 中文注释
- 使用 CSS 变量（`var(--color-primary-500)` 等），不要硬编码颜色
- 优先使用 `components/base/` 下的基础组件（AppCard, TagBadge）
- StockName 和 PriceDisplay 风格本地实现（避免过度封装）
- 项目不在 git 中，直接修改文件
- 最终验证：`cd frontend && npx vite build` 构建通过

---

### Task 1: DateTimeHero 新增 compact prop

**Files:**
- Modify: `src/components/DateTimeHero.vue`

**Interfaces:**
- Consumes: 无（独立组件）
- Produces: 新增 `compact` prop（Boolean，默认 false）；紧凑模式下高度 50-60px，横向布局（左侧状态+日期，右侧时间），浅紫色渐变背景

- [ ] **Step 1: 新增 compact prop 定义**

在 `<script setup>` 的 props 中添加：
```js
const props = defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})
```
注意：当前组件没有显式 `defineProps`，需要用 `defineProps` 包一下。

- [ ] **Step 2: 修改 template 支持紧凑模式**

用 `v-if="compact"` / `v-else` 区分两种布局：
- 紧凑模式：单行 flex，左侧「交易中/休市」状态点 + 日期（如"2026年8月28日 星期四"），右侧 `HH:mm:ss` 时间
- 默认模式：保持现有大横幅布局不变

紧凑模式 template 结构：
```html
<div class="datetime-hero" :class="{ 'is-compact': compact }">
  <template v-if="compact">
    <div class="compact-left">
      <span class="status-dot" :class="{ open: isTradingHours }"></span>
      <span class="compact-date">{{ dateStr }} {{ weekdayStr }}</span>
    </div>
    <div class="compact-time tabular-nums">{{ hourMin }}:{{ second }}</div>
  </template>
  <template v-else>
    <!-- 原有大横幅内容保持不变 -->
  </template>
</div>
```

- [ ] **Step 3: 添加紧凑模式样式**

在 `<style scoped>` 末尾添加：
```css
/* ========== 紧凑模式 ========== */
.datetime-hero.is-compact {
  padding: 0 20px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  color: var(--color-gray-700);
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-gray-200);
}
.datetime-hero.is-compact::before,
.datetime-hero.is-compact::after {
  display: none;
}
.compact-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--font-size-sm);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-gray-400);
  flex-shrink: 0;
}
.status-dot.open {
  background: var(--color-down);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.compact-date {
  font-weight: 500;
  color: var(--color-gray-600);
}
.compact-time {
  font-size: var(--font-size-lg);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--color-primary-600);
  letter-spacing: 0.5px;
}
```

- [ ] **Step 4: 验证构建**

Run: `cd /Users/leungmk/Applications/work/t/stock-analyzer/frontend && npx vite build`
Expected: BUILD SUCCESS

---

### Task 2: 三大指数卡片 AppCard 化 + 颜色条优化

**Files:**
- Modify: `src/views/Dashboard.vue` (三大指数卡片区域，约第 22-108 行 template + 对应 style)

**Interfaces:**
- Consumes: AppCard 组件（`import AppCard from '../components/base/AppCard.vue'`）
- Produces: 三个指数卡片使用 AppCard 容器，顶部有红/绿颜色条，信息密度提升，整体风格统一

- [ ] **Step 1: 引入 AppCard 组件**

在 script setup 顶部 import 中添加：
```js
import AppCard from '../components/base/AppCard.vue'
```

- [ ] **Step 2: 重构单个指数卡片为 AppCard + 颜色条模式**

将三个 `el-col` 中的 `.index-card` 替换为 AppCard 结构。每个卡片：
- 顶部一条 4px 高的颜色条（上涨红 / 下跌绿），放在 AppCard 内部顶部
- header slot 放指数名称（小号、浅灰）
- body 放价格 + 涨跌幅（更大更紧凑）
- 增加 hover 效果和点击跳转（可选，跳转到指数详情或不跳转，保持与之前一致即可）

单卡结构示意：
```html
<AppCard :hover-effect="true" class="index-card-wrap" :class="{ up: ..., down: ... }">
  <template #header>
    <span class="index-name-label">上证指数</span>
  </template>
  <!-- 骨架屏 or 数据 -->
  <div class="index-price-lg tabular-nums">{{ shIndex.price || '--' }}</div>
  <div class="index-chg-row tabular-nums">
    <span>{{ shIndex.change_pct > 0 ? '+' : '' }}{{ shIndex.change_pct }}%</span>
    <span>{{ shIndex.change_pct > 0 ? '+' : '' }}{{ shIndex.change_amount }}</span>
  </div>
</AppCard>
```

颜色条用伪元素实现（`::before`），不要在 template 里加多余 div。

- [ ] **Step 3: 替换对应样式**

删除旧的 `.index-card` 相关样式，新增：
```css
.index-card-wrap {
  position: relative;
  cursor: pointer;
}
.index-card-wrap::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--color-gray-300);
}
.index-card-wrap.up::before { background: var(--color-up); }
.index-card-wrap.down::before { background: var(--color-down); }

.index-name-label {
  font-size: var(--font-size-sm);
  color: var(--color-gray-500);
  font-weight: 500;
}

.index-card-wrap :deep(.app-card__body) {
  padding: var(--spacing-4) var(--spacing-5) var(--spacing-5);
}

.index-price-lg {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: var(--spacing-2);
  color: var(--color-gray-800);
}
.up .index-price-lg { color: var(--color-up); }
.down .index-price-lg { color: var(--color-down); }

.index-chg-row {
  display: flex;
  gap: var(--spacing-4);
  font-size: var(--font-size-sm);
  font-weight: 600;
}
.up .index-chg-row { color: var(--color-up); }
.down .index-chg-row { color: var(--color-down); }
```

- [ ] **Step 4: 验证构建**

Run: `cd /Users/leungmk/Applications/work/t/stock-analyzer/frontend && npx vite build`
Expected: BUILD SUCCESS

---

### Task 3: 新增 AI 今日关注模块

**Files:**
- Modify: `src/views/Dashboard.vue` (在三大指数下方、市场情绪上方插入新模块)

**Interfaces:**
- Consumes: AppCard, TagBadge 组件；`router.push('/stock/:code')` 跳转
- Produces: 「AI 今日关注」模块，3 张横排股票卡片，含名称+代码、价格+涨跌幅、AI 评级徽章、一句话推荐理由

- [ ] **Step 1: 引入 TagBadge 组件**

```js
import TagBadge from '../components/base/TagBadge.vue'
```

- [ ] **Step 2: 定义模拟数据**

在 script setup 中添加：
```js
// AI 今日关注 — 模拟数据（后续接真实 AI 接口）
const aiFocusStocks = ref([
  {
    code: '600519',
    name: '贵州茅台',
    price: 1688.50,
    change: 23.40,
    changePct: 1.41,
    rating: 'A+',
    ratingType: 'danger', // 用上涨红表示强推荐
    reason: '技术面突破，短期趋势向好，量能配合良好'
  },
  {
    code: '300750',
    name: '宁德时代',
    price: 198.60,
    change: -2.30,
    changePct: -1.15,
    rating: 'A',
    ratingType: 'primary',
    reason: '基本面稳健，回调至关键支撑位，中长期配置价值凸显'
  },
  {
    code: '601318',
    name: '中国平安',
    price: 45.82,
    change: 0.65,
    changePct: 1.44,
    rating: 'B+',
    ratingType: 'warning',
    reason: '估值处于历史低位，股息率有吸引力，适合稳健配置'
  }
])

const aiFocusLoading = ref(false)

function refreshAiFocus() {
  // 模拟刷新，后续替换为真实 AI 接口
  aiFocusLoading.value = true
  setTimeout(() => {
    aiFocusLoading.value = false
  }, 800)
}

function goToStock(code) {
  router.push(`/stock/${code}`)
}
```
注意：`goToStock` 函数已存在于 Dashboard 中，确认无重复。

- [ ] **Step 3: 在 template 中插入模块**

在「三大指数卡片」区块之后、「指数加载失败提示」之前插入：
```html
<!-- AI 今日关注 -->
<AppCard class="ai-focus-card" :shadow="true">
  <template #header>
    <div class="section-title-group">
      <div class="section-title">
        <span class="ai-dot"></span>
        AI 今日关注
      </div>
      <div class="section-subtitle">基于自选股的智能精选</div>
    </div>
  </template>
  <template #extra>
    <el-button
      type="primary"
      link
      :loading="aiFocusLoading"
      @click="refreshAiFocus"
    >
      <el-icon><Refresh /></el-icon>
    </el-button>
  </template>
  <el-row :gutter="16" class="ai-focus-row">
    <el-col :span="8" v-for="stock in aiFocusStocks" :key="stock.code">
      <div
        class="ai-stock-card"
        @click="goToStock(stock.code)"
        :class="{ 'is-loading': aiFocusLoading }"
      >
        <div class="ai-stock-top">
          <div class="stock-name-style">
            <span class="stock-name-text">{{ stock.name }}</span>
            <span class="stock-name-code">{{ stock.code }}</span>
          </div>
          <TagBadge :type="stock.ratingType" size="sm">{{ stock.rating }}</TagBadge>
        </div>
        <div class="ai-stock-price tabular-nums" :class="{ up: stock.change >= 0, down: stock.change < 0 }">
          {{ stock.price.toFixed(2) }}
        </div>
        <div class="ai-stock-change tabular-nums" :class="{ up: stock.change >= 0, down: stock.change < 0 }">
          <span>{{ stock.change >= 0 ? '+' : '' }}{{ stock.change.toFixed(2) }}</span>
          <span>{{ stock.changePct >= 0 ? '+' : '' }}{{ stock.changePct.toFixed(2) }}%</span>
        </div>
        <div class="ai-stock-reason">
          <span class="reason-quote">"</span>
          {{ stock.reason }}
          <span class="reason-quote">"</span>
        </div>
      </div>
    </el-col>
  </el-row>
</AppCard>
```

- [ ] **Step 4: 添加样式**

在 style 末尾添加：
```css
/* AI 今日关注 */
.ai-focus-card {
  margin-bottom: 20px;
}

.section-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-gray-800);
}
.ai-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-secondary-500));
  box-shadow: 0 0 6px rgba(124, 58, 237, 0.5);
}
.section-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
  font-weight: 400;
}

.ai-focus-row {
  margin-top: 0;
}
.ai-stock-card {
  background: var(--color-gray-50);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: all var(--transition-normal);
}
.ai-stock-card:hover {
  background: #fff;
  border-color: var(--color-primary-200);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.ai-stock-card.is-loading {
  opacity: 0.6;
  pointer-events: none;
}

.ai-stock-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-3);
}
.stock-name-style {
  display: inline-flex;
  align-items: baseline;
  gap: var(--spacing-2);
}
.stock-name-text {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-gray-800);
}
.stock-name-code {
  font-family: 'SF Mono', Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  color: var(--color-gray-400);
}

.ai-stock-price {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 2px;
}
.ai-stock-price.up { color: var(--color-up); }
.ai-stock-price.down { color: var(--color-down); }

.ai-stock-change {
  display: flex;
  gap: var(--spacing-3);
  font-size: var(--font-size-xs);
  font-weight: 500;
  margin-bottom: var(--spacing-3);
}
.ai-stock-change.up { color: var(--color-up); }
.ai-stock-change.down { color: var(--color-down); }

.ai-stock-reason {
  font-size: var(--font-size-xs);
  color: var(--color-gray-600);
  line-height: 1.5;
  padding-top: var(--spacing-3);
  border-top: 1px dashed var(--color-gray-200);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.reason-quote {
  color: var(--color-primary-400);
  font-family: Georgia, serif;
  font-size: 16px;
  line-height: 0;
}
```

- [ ] **Step 5: 验证构建**

Run: `cd /Users/leungmk/Applications/work/t/stock-analyzer/frontend && npx vite build`
Expected: BUILD SUCCESS

---

### Task 4: 市场情绪 + 热门板块 AppCard 化

**Files:**
- Modify: `src/views/Dashboard.vue` (市场情绪 + 热门板块双栏区域，约第 117-221 行)

**Interfaces:**
- Consumes: AppCard 组件
- Produces: 左右两栏都改用 AppCard，市场情绪视觉更精致，热门板块列表优化

- [ ] **Step 1: 将市场情绪 el-card 替换为 AppCard**

结构：
- header slot: 图标 + "市场情绪" 文字
- body: 保持原有 2 行 x 3 列的统计数据，优化样式（更精致的卡片风格）
- 移除 `el-card` 和 `card-shadow` class

header 结构：
```html
<template #header>
  <div class="card-header">
    <el-icon color="var(--color-warning)"><DataLine /></el-icon>
    <span>市场情绪</span>
  </div>
</template>
```

- [ ] **Step 2: 将热门板块 el-card 替换为 AppCard**

结构：
- header slot: 图标 + "热门板块"
- extra slot: 刷新按钮 + 查看全部按钮
- body: 板块列表（保持现有列表结构与排名序号）
- 保持 skeleton、error、data 三种状态

- [ ] **Step 3: 优化市场情绪数据样式**

将 stat-item 调整得更精致：数值更紧凑、标签更小、分隔线用浅灰虚线。保持 6 个数据不变。

- [ ] **Step 4: 优化热门板块列表项**

保持现有的排名序号 + 名称 + 领涨股 + 涨跌幅结构，微调间距和字号使其更紧凑精致。
涨跌幅字号适当增大，突出显示。

- [ ] **Step 5: 更新相关样式**

删除旧的 `.stats-card`、`.board-card` 相关 el-card 样式，替换为 AppCard 兼容的样式。保持所有数据项功能不变。

- [ ] **Step 6: 验证构建**

Run: `cd /Users/leungmk/Applications/work/t/stock-analyzer/frontend && npx vite build`
Expected: BUILD SUCCESS

---

### Task 5: AI 市场点评卡片 AppCard 化

**Files:**
- Modify: `src/views/Dashboard.vue` (AI 点评卡片区域，约第 223-244 行)

**Interfaces:**
- Consumes: AppCard 组件
- Produces: AI 点评卡片改用 AppCard，增加 AI 标识，生成中状态更明确，流式输出功能保持不变

- [ ] **Step 1: 将 AI 点评 el-card 替换为 AppCard**

结构：
- header slot: AI 紫色图标 + "AI 市场点评" 标题 + 生成中标签
- extra slot: 重新生成按钮
- body: 点评内容（流式输出）

- [ ] **Step 2: 优化生成中状态**

生成中时：
- 显示更明确的"AI 正在生成中..."提示
- 有动态的 typing 指示（三个跳动的点）
- 重新生成按钮 disabled + loading

- [ ] **Step 3: 调整样式**

保持紫色渐变氛围但适配 AppCard 结构。用 `:deep()` 调整 `app-card__body` padding。

- [ ] **Step 4: 验证构建**

Run: `cd /Users/leungmk/Applications/work/t/stock-analyzer/frontend && npx vite build`
Expected: BUILD SUCCESS

---

### Task 6: Dashboard 中切换 DateTimeHero 为紧凑模式 + 最终构建验证

**Files:**
- Modify: `src/views/Dashboard.vue` (DateTimeHero 使用方式)

**Interfaces:**
- Consumes: DateTimeHero compact prop
- Produces: 首页顶部使用紧凑 DateTimeHero

- [ ] **Step 1: 将 DateTimeHero 改为 compact 模式**

将 `<DateTimeHero />` 改为 `<DateTimeHero :compact="true" />`，放在页面顶部（page-header 之后或替换原位置）。

- [ ] **Step 2: 调整页面布局顺序**

页面结构从上到下应为：
1. page-header（市场概览标题 + 搜索入口）
2. DateTimeHero compact（紧凑信息条）
3. 三大指数卡片
4. AI 今日关注（新增模块）
5. 市场情绪 + 热门板块双栏
6. AI 市场点评

- [ ] **Step 3: 完整构建验证**

Run: `cd /Users/leungmk/Applications/work/t/stock-analyzer/frontend && npx vite build`
Expected: BUILD SUCCESS with no errors

- [ ] **Step 4: 功能完整性自查清单**

- [ ] DateTimeHero 紧凑模式正常显示（状态点+日期+时间）
- [ ] 三大指数卡片 AppCard 风格 + 颜色条
- [ ] AI 今日关注 3 张卡片显示，点击跳转股票详情
- [ ] 市场情绪 + 热门板块 AppCard 风格，数据正常
- [ ] AI 市场点评 AppCard 风格，流式输出正常
- [ ] 所有现有加载/错误状态正常
- [ ] 响应式布局不崩坏
- [ ] 无硬编码颜色（全部使用 CSS 变量）
