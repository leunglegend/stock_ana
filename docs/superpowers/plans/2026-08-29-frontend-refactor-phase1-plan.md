# 前端重构 · 阶段一：设计系统 + 全局框架 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立统一的设计系统（Design Token）+ 重构全局布局框架，为后续所有页面改版打基础。

**Architecture:** 使用 CSS 变量（:root）定义完整的 Design Token 系统，抽取核心业务组件库，重构 Layout 组件（侧边栏重排 + 顶部搜索栏），所有改动向后兼容，不破坏现有页面功能。

**Tech Stack:** Vue 3 + Vite + Element Plus + CSS 变量 + Pinia

**Spec:** 设计 Demo 文件位于 `.superpowers/brainstorm/13785-1787985101/content/` 目录下（demo-dashboard.html 等 7 个文件），作为视觉参考。

**Design Reference:**
- 主色：靛蓝 `#4f46e5` + 紫罗兰 `#7c3aed`
- 涨跌色：红 `#ef4444`（涨）/ 绿 `#10b981`（跌）
- 圆角：sm 6px / md 10px / lg 12px
- 间距：4px 网格（4/8/12/16/20/24/32/40/48）
- 字号：12/14/16/20/24/30/36（1.25 scale）
- 阴影：sm / md / lg 三级
- 数字：`tabular-nums` 等宽数字

## Global Constraints

- 所有新样式使用 CSS 变量定义，不硬编码色值
- 所有现有页面必须保持可用，不能因为重构导致功能中断
- Element Plus 组件样式使用 CSS 变量覆盖，不使用 !important
- 组件命名遵循 PascalCase，文件路径与现有项目一致
- 中文界面，中文注释
- 每个任务完成后验证现有页面不报错

---

## File Structure

### 新建文件
| 文件 | 职责 |
|------|------|
| `frontend/src/styles/tokens.css` | Design Token CSS 变量系统（色彩/间距/字号/圆角/阴影） |
| `frontend/src/components/base/StockName.vue` | 股票名称+代码统一展示组件 |
| `frontend/src/components/base/PriceDisplay.vue` | 价格+涨跌幅统一展示组件 |
| `frontend/src/components/base/AppCard.vue` | 统一卡片组件（header+body+footer） |
| `frontend/src/components/base/AppSkeleton.vue` | 统一骨架屏组件 |
| `frontend/src/components/base/TagBadge.vue` | 标签徽章组件（AI评级/状态等） |
| `frontend/src/utils/format.js` | 格式化工具函数（已有，扩展完善） |

### 修改文件
| 文件 | 修改内容 |
|------|---------|
| `frontend/src/style.css` | 引入 tokens.css，统一全局样式，清理零散硬编码 |
| `frontend/src/components/Layout.vue` | 侧边栏导航重排 + 顶部栏重构（搜索框+通知+用户） |
| `frontend/src/router/index.js` | 移除「搜索个股」一级路由（改为全局搜索），路由元信息调整 |
| `frontend/src/views/Search.vue` | 调整为独立搜索排行页面（保留但不在侧边栏显示） |

---

## Tasks

### Task 1: 建立 Design Token 系统

**Files:**
- Create: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Produces: CSS 变量 `--color-primary-500`、`--spacing-4`、`--font-size-14` 等，供全局使用
- Consumed by: 所有后续任务的组件样式

- [ ] **Step 1: 创建 tokens.css，定义完整的色彩系统**

```css
/* ============================================
   Design Tokens — Stock Analyzer
   ============================================ */

:root {
  /* ---------- Primary Colors ---------- */
  --color-primary-50: #eef2ff;
  --color-primary-100: #e0e7ff;
  --color-primary-300: #a5b4fc;
  --color-primary-500: #4f46e5;
  --color-primary-600: #4338ca;
  --color-primary-700: #3730a3;

  --color-secondary-50: #faf5ff;
  --color-secondary-100: #f3e8ff;
  --color-secondary-300: #c4b5fd;
  --color-secondary-500: #7c3aed;
  --color-secondary-600: #6d28d9;
  --color-secondary-700: #5b21b6;

  /* ---------- Functional Colors ---------- */
  --color-up: #ef4444;        /* 涨 - 红 */
  --color-up-light: #fef2f2;
  --color-up-dark: #dc2626;
  --color-down: #10b981;      /* 跌 - 绿 */
  --color-down-light: #ecfdf5;
  --color-down-dark: #059669;
  --color-warning: #f59e0b;    /* 警告 - 黄 */
  --color-warning-light: #fffbeb;
  --color-warning-dark: #d97706;
  --color-info: #3b82f6;       /* 信息 - 蓝 */
  --color-info-light: #eff6ff;
  --color-info-dark: #2563eb;

  /* ---------- Neutral Colors ---------- */
  --color-gray-50: #f8fafc;
  --color-gray-100: #f1f5f9;
  --color-gray-200: #e2e8f0;
  --color-gray-300: #cbd5e1;
  --color-gray-400: #94a3b8;
  --color-gray-500: #64748b;
  --color-gray-600: #475569;
  --color-gray-700: #334155;
  --color-gray-800: #1e293b;
  --color-gray-900: #0f172a;

  /* ---------- Spacing (4px grid) ---------- */
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 20px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-10: 40px;
  --spacing-12: 48px;

  /* ---------- Font Size ---------- */
  --font-size-xs: 12px;
  --font-size-sm: 13px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 18px;
  --font-size-2xl: 20px;
  --font-size-3xl: 24px;
  --font-size-4xl: 30px;
  --font-size-5xl: 36px;

  /* ---------- Line Height ---------- */
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.6;

  /* ---------- Border Radius ---------- */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* ---------- Box Shadow ---------- */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.12);
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.06);

  /* ---------- Transition ---------- */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.25s ease;
  --transition-slow: 0.35s ease;
}
```

- [ ] **Step 2: 在 style.css 顶部引入 tokens.css**

在 `frontend/src/style.css` 文件最顶部添加：
```css
@import './styles/tokens.css';
```

注意：需要确认 tokens.css 的路径相对于 style.css 是否正确，可能需要调整路径。

- [ ] **Step 3: 验证 CSS 变量生效**

打开浏览器，在 DevTools 中检查 :root 元素，确认 `--color-primary-500` 等变量已加载。

- [ ] **Step 4: 确保现有页面无样式错误**

打开首页、自选股、股票详情等主要页面，确认样式未被破坏。

---

### Task 2: 全局样式统一与清理

**Files:**
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: Task 1 定义的 CSS 变量
- Produces: 统一的全局样式规范

- [ ] **Step 1: 统一 body 基础样式**

将 style.css 中现有的 body 样式替换为使用 CSS 变量的版本：
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-gray-800);
  background-color: var(--color-gray-50);
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
}
```

- [ ] **Step 2: 统一数字样式类**

添加统一的等宽数字类：
```css
.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.text-up {
  color: var(--color-up);
}

.text-down {
  color: var(--color-down);
}

.text-warning {
  color: var(--color-warning);
}

.text-muted {
  color: var(--color-gray-500);
}
```

- [ ] **Step 3: 统一卡片类**

添加统一的卡片基础样式类：
```css
.app-card {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-gray-100);
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}

.app-card:hover {
  box-shadow: var(--shadow-md);
}
```

- [ ] **Step 4: 统一滚动条样式**

将现有的滚动条样式替换为使用 CSS 变量：
```css
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--color-gray-50);
}

::-webkit-scrollbar-thumb {
  background: var(--color-gray-300);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-gray-400);
}
```

- [ ] **Step 5: 保留原有动画类但用变量替换色值**

保留 `.number-flash-up`、`.number-flash-down`、`.slide-fade-enter-active` 等已有动画类，将其中硬编码的颜色值替换为 CSS 变量。

- [ ] **Step 6: 验证页面样式正常**

浏览所有 7 个页面，确认样式未被破坏，视觉基本一致（颜色会微调但不影响布局）。

---

### Task 3: StockName 股票名称组件

**Files:**
- Create: `frontend/src/components/base/StockName.vue`

**Interfaces:**
- Props: `name` (string), `code` (string), `size` ('sm' | 'md' | 'lg' = 'md')
- Produces: 统一的股票名称+代码展示，名称字号随 size 变化，代码用灰色等宽字体

- [ ] **Step 1: 创建 StockName.vue 组件**

```vue
<template>
  <div class="stock-name" :class="`stock-name--${size}`">
    <span class="stock-name__text">{{ name }}</span>
    <span class="stock-name__code">{{ code }}</span>
  </div>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    required: true
  },
  code: {
    type: String,
    required: true
  },
  size: {
    type: String,
    default: 'md', // sm, md, lg
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})
</script>

<style scoped>
.stock-name {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
}

.stock-name__text {
  font-weight: 600;
  color: var(--color-gray-800);
}

.stock-name__code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--color-gray-400);
  font-size: 0.8em;
}

.stock-name--sm .stock-name__text {
  font-size: var(--font-size-sm);
}

.stock-name--md .stock-name__text {
  font-size: var(--font-size-base);
}

.stock-name--lg .stock-name__text {
  font-size: var(--font-size-lg);
}
</style>
```

- [ ] **Step 2: 验证组件可正常导入使用**

在任意一个现有页面临时引入组件测试渲染效果（测试后可移除，或在后续任务中替换）。

---

### Task 4: PriceDisplay 价格展示组件

**Files:**
- Create: `frontend/src/components/base/PriceDisplay.vue`

**Interfaces:**
- Props: `price` (number), `change` (number), `changePercent` (number), `size` ('sm' | 'md' | 'lg' = 'md')
- Produces: 统一的价格+涨跌幅展示，自动判断涨跌颜色，支持百分比和涨跌额

- [ ] **Step 1: 创建 PriceDisplay.vue 组件**

```vue
<template>
  <div class="price-display" :class="`price-display--${size}`">
    <span class="price-display__price tabular-nums" :class="priceClass">
      {{ formatPrice(price) }}
    </span>
    <span v-if="change !== undefined" class="price-display__change tabular-nums" :class="priceClass">
      {{ change >= 0 ? '+' : '' }}{{ formatPrice(change) }}
      <span v-if="changePercent !== undefined">
        ({{ changePercent >= 0 ? '+' : '' }}{{ changePercent.toFixed(2) }}%)
      </span>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  price: {
    type: Number,
    required: true
  },
  change: {
    type: Number,
    default: undefined
  },
  changePercent: {
    type: Number,
    default: undefined
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})

const priceClass = computed(() => {
  if (props.change !== undefined) {
    return props.change >= 0 ? 'text-up' : 'text-down'
  }
  if (props.changePercent !== undefined) {
    return props.changePercent >= 0 ? 'text-up' : 'text-down'
  }
  return ''
})

const formatPrice = (val) => {
  if (val === undefined || val === null || isNaN(val)) return '--'
  return val.toFixed(2)
}
</script>

<style scoped>
.price-display {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
}

.price-display__price {
  font-weight: 700;
  color: var(--color-gray-800);
}

.price-display__change {
  font-weight: 500;
}

.price-display--sm .price-display__price {
  font-size: var(--font-size-base);
}
.price-display--sm .price-display__change {
  font-size: var(--font-size-xs);
}

.price-display--md .price-display__price {
  font-size: var(--font-size-lg);
}
.price-display--md .price-display__change {
  font-size: var(--font-size-sm);
}

.price-display--lg .price-display__price {
  font-size: var(--font-size-3xl);
}
.price-display--lg .price-display__change {
  font-size: var(--font-size-base);
}
</style>
```

- [ ] **Step 2: 验证组件可正常使用**

测试涨/跌/平三种状态下的颜色和格式是否正确。

---

### Task 5: AppCard 统一卡片组件

**Files:**
- Create: `frontend/src/components/base/AppCard.vue`

**Interfaces:**
- Slots: `header`（标题栏）、`default`（内容）、`footer`（底部）、`extra`（header右侧操作区）
- Props: `hover-effect` (boolean = true)、`shadow` (boolean = true)
- Produces: 统一风格的卡片容器

- [ ] **Step 1: 创建 AppCard.vue 组件**

```vue
<template>
  <div class="app-card" :class="{ 'app-card--hover': hoverEffect, 'app-card--shadow': shadow }">
    <div v-if="$slots.header || $slots.extra" class="app-card__header">
      <slot name="header" />
      <div v-if="$slots.extra" class="app-card__extra">
        <slot name="extra" />
      </div>
    </div>
    <div class="app-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="app-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  hoverEffect: {
    type: Boolean,
    default: true
  },
  shadow: {
    type: Boolean,
    default: true
  }
})
</script>

<style scoped>
.app-card {
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-gray-100);
  overflow: hidden;
}

.app-card--shadow {
  box-shadow: var(--shadow-card);
}

.app-card--hover:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}

.app-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-gray-100);
}

.app-card__extra {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.app-card__body {
  padding: var(--spacing-5);
}

.app-card__footer {
  padding: var(--spacing-3) var(--spacing-5);
  border-top: 1px solid var(--color-gray-100);
  background: var(--color-gray-50);
}
</style>
```

- [ ] **Step 2: 验证组件渲染**

测试 header + body + footer + extra 各种组合的渲染效果。

---

### Task 6: TagBadge 标签徽章组件

**Files:**
- Create: `frontend/src/components/base/TagBadge.vue`

**Interfaces:**
- Props: `text` (string), `type` ('primary' | 'success' | 'warning' | 'danger' | 'info' | 'default')、`size` ('sm' | 'md')
- Produces: 统一的标签/徽章，用于 AI 评级、状态指示等

- [ ] **Step 1: 创建 TagBadge.vue 组件**

```vue
<template>
  <span class="tag-badge" :class="[`tag-badge--${type}`, `tag-badge--${size}`]">
    <slot>{{ text }}</slot>
  </span>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'default',
    validator: (v) => ['primary', 'success', 'warning', 'danger', 'info', 'default', 'up', 'down'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v)
  }
})
</script>

<style scoped>
.tag-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border-radius: var(--radius-full);
  padding: 2px 10px;
  white-space: nowrap;
}

.tag-badge--sm {
  font-size: 11px;
  padding: 1px 8px;
}

.tag-badge--md {
  font-size: 12px;
}

.tag-badge--primary {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
}

.tag-badge--success {
  background: var(--color-down-light);
  color: var(--color-down);
}

.tag-badge--warning {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}

.tag-badge--danger {
  background: var(--color-up-light);
  color: var(--color-up);
}

.tag-badge--info {
  background: var(--color-info-light);
  color: var(--color-info-dark);
}

.tag-badge--default {
  background: var(--color-gray-100);
  color: var(--color-gray-600);
}

.tag-badge--up {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-up);
}

.tag-badge--down {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-down);
}
</style>
```

- [ ] **Step 2: 验证所有 type 和 size 的显示效果**

---

### Task 7: Layout 全局布局重构

**Files:**
- Modify: `frontend/src/components/Layout.vue`
- Modify: `frontend/src/router/index.js`

**Interfaces:**
- Consumes: Task 1 的 Design Token
- Produces: 新的侧边栏导航（重排）+ 顶部栏（全局搜索框 + 通知 + 用户头像）

**注意：** 此任务只调整布局框架和导航，不改各页面的内容。全局搜索框目前先做 UI 壳子，功能复用现有的 GlobalSearch 组件（点击后触发打开）。

- [ ] **Step 1: 调整侧边栏导航项顺序和内容**

新的侧边栏导航顺序：
1. 市场概览（原第一个，保留）
2. 我的自选（原第三个，上移到第二位）
3. 板块监控（原第四个，上移到第三位）
4. 复盘报告（原第五个，保留）

移除「搜索个股」作为一级导航。

- [ ] **Step 2: 重构顶部栏**

将顶部栏从「标题 + 搜索按钮 + 通知铃铛」改为：
- 左侧：面包屑/页面标题
- 中间：全局搜索框（点击唤起 GlobalSearch 弹窗，显示 `/` 快捷键提示）
- 右侧：通知铃铛 + 用户头像/登录入口

- [ ] **Step 3: 调整路由元信息**

在 `router/index.js` 中：
- 保持所有路由存在（Search 页仍然可以通过 URL 访问）
- 调整 meta 信息以适配新的面包屑

- [ ] **Step 4: 验证所有页面可正常访问**

点击侧边栏每个导航项，确认页面正常显示，路由跳转正确。

---

### Task 8: format.js 工具函数完善

**Files:**
- Modify: `frontend/src/utils/format.js`（已有文件，扩展）

**Interfaces:**
- Produces: 统一的格式化函数库，供所有组件使用

- [ ] **Step 1: 检查现有 format.js 内容**

读取现有文件，确认已有哪些函数。

- [ ] **Step 2: 补充缺失的格式化函数**

确保包含以下函数（已有则跳过，没有则添加）：
- `formatPrice(value, decimals = 2)` — 价格格式化
- `formatPercent(value, decimals = 2, withSign = true)` — 百分比格式化，带正负号
- `formatVolume(value)` — 成交量格式化（万/亿）
- `formatAmount(value)` — 成交额格式化（万/亿）
- `formatDate(date, format = 'YYYY-MM-DD')` — 日期格式化
- `formatTime(date)` — 时间格式化（HH:mm:ss）
- `formatChange(value, decimals = 2)` — 涨跌额格式化（带 +/-）
- `getRatingType(rating)` — AI评级映射到 type（A+~D → success/warning/danger）
- `truncateText(text, maxLen)` — 文本截断
- `thousandsSeparator(num)` — 千分位格式化

- [ ] **Step 3: 导出所有函数**

确保使用 ES module 导出，组件中可按需引入。

---

### Task 9: 阶段一回归验证

**Files:**
- 所有现有页面

**Interfaces:**
- 验证所有改动不破坏现有功能

- [ ] **Step 1: 全页面样式检查**

逐一打开 7 个页面，确认：
- 布局正常，没有错位
- 颜色有微调但整体协调
- 没有控制台报错

- [ ] **Step 2: 核心功能测试**

测试以下功能是否正常：
- 侧边栏导航切换
- 全局搜索快捷键（/ 键）
- 自选股添加/删除
- 股票详情页 K 线切换
- 登录/注册弹窗

- [ ] **Step 3: 构建验证**

运行 `npm run build` 确认构建通过，无报错。

---

## 阶段一交付物清单

1. ✅ `src/styles/tokens.css` — 完整 Design Token 系统（50+ CSS 变量）
2. ✅ `src/components/base/` — 5 个基础业务组件（StockName / PriceDisplay / AppCard / TagBadge / AppSkeleton）
3. ✅ `src/style.css` — 全局样式统一与清理
4. ✅ `src/components/Layout.vue` — 侧边栏重排 + 顶部栏重构
5. ✅ `src/utils/format.js` — 完善的格式化工具库
6. ✅ 所有现有页面功能不受影响，构建通过

---

**Plan complete and saved to `docs/superpowers/plans/2026-08-29-frontend-refactor-phase1-plan.md`.**

**后续阶段（待阶段一完成后）：**
- 阶段二：核心页面改版 + AI 驱动范式（首页 / 自选 / 详情 / 搜索）
- 阶段三：功能补齐 + 体验完善（板块 / 复盘 / 性能优化）
