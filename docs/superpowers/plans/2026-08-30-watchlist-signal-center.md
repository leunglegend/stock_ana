# Watchlist Signal Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在自选页面增加用户主动触发、结果可解释且支持部分失败的技术信号中心。

**Architecture:** 纯函数模块负责从 K 线和成本收益计算信号；组合式函数负责受控并发、进度和分组隔离；展示组件只消费已归一化结果。现有自选行情加载逻辑保持不变。

**Tech Stack:** Vue 3、Element Plus、Node.js `node:test`、现有并发工具与股票 API

---

### Task 1: 信号计算引擎

**Files:**
- Create: `frontend/src/utils/stockSignals.js`
- Create: `frontend/tests/stock-signals.test.js`

- [ ] 先编写趋势、MACD 交叉、RSI、突破、回撤、成本及缺失数据测试。
- [ ] 运行 `node --test tests/stock-signals.test.js`，确认因模块缺失而失败。
- [ ] 实现 `analyzeStockSignals(klineData, context)` 与明确的信号对象结构。
- [ ] 重跑测试并确认通过。

### Task 2: 扫描状态与受控并发

**Files:**
- Create: `frontend/src/components/watchlist/useWatchlistSignals.js`
- Modify: `frontend/tests/stock-signals.test.js`

- [ ] 为结果汇总 `summarizeSignalResults()` 编写失败测试。
- [ ] 实现并验证偏强、中性、关注、失败计数。
- [ ] 实现 `useWatchlistSignals()`：并发 3、逐项更新、请求代际隔离、分组变化清空。

### Task 3: 信号中心界面

**Files:**
- Create: `frontend/src/components/watchlist/WatchlistSignalCenter.vue`
- Modify: `frontend/src/views/Watchlist.vue`

- [ ] 新增可访问的扫描按钮、进度、汇总指标、部分失败提示和结果列表。
- [ ] 将当前分组股票与行情行传入扫描组合式函数。
- [ ] 在分组 Tab 与筛选区之间接入组件。

### Task 4: 验证

- [ ] 运行 `cd frontend && node --test tests/*.test.js`。
- [ ] 运行 `cd frontend && npm run build`。
- [ ] 启动 Vite，验证桌面和移动端无溢出，扫描入口与状态完整。
- [ ] 运行 `git diff --check` 并检查改动边界；未经明确许可不提交 Git。

