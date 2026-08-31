# 全站重点数字科技感增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一放大研究台全站重点数字，并以主题语义色强化科技终端视觉层级。

**Architecture:** 以 `MetricCell`、`PriceDisplay`、`PercentageDisplay` 三个共享数字组件为主改动面，补充雷达/看板/报告等页面专用统计值的 Token 化强调。所有颜色继续来自 `--text-*`、`--color-*` 语义变量，不改数据和布局。

**Tech Stack:** Vue 3、CSS custom properties、Node.js test runner、Vite。

---

### Task 1: 补充数字层级回归契约

**Files:**
- Modify: `frontend/tests/new-feature-style-contract.test.js`

- [x] **Step 1: 添加共享数字样式断言**

新增测试读取 `MetricCell.vue`、`PriceDisplay.vue`、`PercentageDisplay.vue`，断言主数字使用等宽字形、增强字号、语义颜色，并禁止 raw hex：

```js
const metricSource = await readFile(new URL('../src/components/base/MetricCell.vue', import.meta.url), 'utf8')
const priceSource = await readFile(new URL('../src/components/base/PriceDisplay.vue', import.meta.url), 'utf8')
const percentageSource = await readFile(new URL('../src/components/base/PercentageDisplay.vue', import.meta.url), 'utf8')

test('共享重点数字采用科技终端层级', () => {
  assert.match(metricSource, /font-family:\s*var\(--font-family-mono\)/)
  assert.match(metricSource, /font-size:\s*var\(--font-size-3xl\)/)
  assert.match(metricSource, /font-weight:\s*700/)
  assert.match(metricSource, /color:\s*var\(--text-positive\)/)
  assert.match(metricSource, /color:\s*var\(--text-negative\)/)
  assert.match(priceSource, /font-family:\s*var\(--font-family-mono\)/)
  assert.match(priceSource, /\.price-display--md \.price-display__price[\s\S]*font-size:\s*var\(--font-size-2xl\)/)
  assert.match(percentageSource, /\.percentage-display--md[\s\S]*font-size:\s*var\(--font-size-2xl\)/)
  assert.doesNotMatch(metricSource + priceSource + percentageSource, /color:\s*#[0-9a-f]{3,8}/i)
})
```

- [x] **Step 2: 运行定向测试确认先失败**

Run: `cd frontend && node --test tests/new-feature-style-contract.test.js`

Expected: 新增测试失败，提示当前共享数字字号/字形尚未达到科技终端层级。

### Task 2: 实现共享数字组件的字号与颜色层级

**Files:**
- Modify: `frontend/src/components/base/MetricCell.vue`
- Modify: `frontend/src/components/base/PriceDisplay.vue`
- Modify: `frontend/src/components/base/PercentageDisplay.vue`

- [x] **Step 1: 提升 MetricCell 主值**

将 `.metric-cell__value` 调整为 `font-family: var(--font-family-mono)`、`font-size: var(--font-size-3xl)`、`font-weight: 700`；单位保持次级字号。正负 tone 改用 `var(--text-positive)` 与 `var(--text-negative)`，中性改用 `var(--text-primary)`。

- [x] **Step 2: 提升 PriceDisplay 主价格**

为 `.price-display__price` 添加 `font-family: var(--font-family-mono)`；将 md 主价格提升至 `var(--font-size-2xl)`、lg 提升至 `var(--font-size-4xl)`，sm 保持可扫描的 `var(--font-size-xl)`。涨跌辅助值继续使用较小字号与现有语义色。

- [x] **Step 3: 提升 PercentageDisplay**

将 sm 保持 `var(--font-size-base)`，md 调整为 `var(--font-size-2xl)`，lg 调整为 `var(--font-size-4xl)`；统一补充 `font-family: var(--font-family-mono)` 和 `font-weight: 700`。

- [x] **Step 4: 运行定向测试确认通过**

Run: `cd frontend && node --test tests/new-feature-style-contract.test.js tests/theme.test.js`

Expected: 所有定向契约测试通过。

### Task 3: 收敛页面专用重点数字并验证正式入口

**Files:**
- Modify when needed: `frontend/src/views/OpportunityRadar.vue`
- Modify when needed: `frontend/src/components/radar/BoardSnapshot.vue`
- Modify when needed: `frontend/src/views/Dashboard.vue`
- Modify when needed: `frontend/src/components/AiAdvice.vue`

- [x] **Step 1: 将页面专用数字对齐共享层级**

仅对现有 `.summary-value`、`.score-value`、`.metric-cell__value` 等数字选择器提升到已有 Token，并使用 `var(--font-family-mono)`；不改普通正文、标签或表格行密度。

- [x] **Step 2: 运行前端完整测试和构建**

Run: `cd frontend && node --test tests/*.test.js && npm run build`

Expected: 全部测试通过，Vite 构建成功；允许记录既有大 chunk 警告。

- [x] **Step 3: 更新 52764 正式入口并做资源检查**

Run: `curl -sS http://localhost:52764/` 获取 index，再请求其 CSS 资源并检查 `font-family:var(--font-family-mono)`、`font-size:var(--font-size-2xl)` 等编译结果；同时访问 `http://localhost:52764/health`。

Expected: 正式入口返回最新构建资源，健康检查返回 `{"status":"ok"}`。
