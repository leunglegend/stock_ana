# 研究台多皮肤与边框可读性 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为研究台接入三套可持久化皮肤，并提升全站工作面边框的视觉可读性。

**Architecture:** 复用现有 `data-theme`、主题 localStorage 和主题变更事件；所有主题差异集中在 Token 层，命令栏只负责选择和反馈。边框调整集中在共享 Token、Element Plus 适配和基础面板，页面组件不复制颜色规则。

**Tech Stack:** Vue 3、Element Plus、CSS custom properties、Node.js test runner、Vite、Playwright。

---

### Task 1: 先写主题和边框回归契约

**Files:**
- Modify: `frontend/tests/theme.test.js`
- Modify: `frontend/tests/new-feature-style-contract.test.js`

- [x] 断言三套主题都有非空的 `data-theme` Token 覆盖。
- [x] 断言主题入口包含桌面按钮、移动更多菜单和三套主题名称。
- [x] 断言 `--border-subtle`、`--border-default`、`--border-strong` 在主题中均有可见差异。
- [x] 运行定向测试，确认实现后的回归契约通过。

### Task 2: 集中实现三套主题 Token 和边框层级

**Files:**
- Modify: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/styles/element-plus.css`
- Modify: `frontend/src/components/base/SectionPanel.vue`

- [x] 保持 Ocean 为默认根 Token，并为 Jade/Charcoal 添加完整语义覆盖。
- [x] 提升工作区外框和主列分隔线对比度，但保留数据行的轻量分隔和无阴影研究台表面。
- [x] 统一 Element Plus 表格、输入、Tab、分页和弹层边框消费语义 Token。
- [x] 运行主题和样式契约测试。

### Task 3: 恢复主题选择入口并接入持久化

**Files:**
- Modify: `frontend/src/components/app/CommandBarUtilities.vue`
- Modify: `frontend/src/theme.js` only if fallback metadata needs adjustment

- [x] 桌面展示主题下拉入口，显示色板、主题名和当前勾选状态。
- [x] 移动更多菜单展示三个主题选择项，保持登录/退出操作。
- [x] 选择后立即调用现有 `applyTheme`，不复制 localStorage 逻辑。
- [x] 保持键盘、焦点和 aria-label 行为。

### Task 4: 全站视觉审计与整合修复

**Files:**
- Modify only when findings require: `frontend/src/views/*.vue`, `frontend/src/components/**/*.vue`, `frontend/src/style.css`

- [x] 扫描页面中的固定颜色、未定义 Token、低对比边框和常规阴影。
- [x] 在三套主题下检查市场、板块、雷达、自选、个股、搜索、报告页面。
- [x] 保持平板雷达单列修复和移动端无横向溢出。

### Task 5: 全量验证

- [x] 运行 `cd frontend && node --test tests/*.test.js`（159 项通过）。
- [x] 运行 `cd frontend && npm run build`（成功；仅有既有大 chunk 提示）。
- [x] 运行 `source backend/venv/bin/activate && cd backend && python -m pytest -q`（17 passed，5 warnings）。
- [x] 运行 `git diff --check`。
- [x] 通过 `http://localhost:52766` 检查视觉伴侣皮肤选择页；项目正式入口 `http://localhost:52764` 验证主题切换与边框 Token。
