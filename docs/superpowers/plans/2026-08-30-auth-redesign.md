# 登录 / 注册页重设计实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变认证流程的前提下，将 `LoginModal.vue` 重做为 A「信号分栏」视觉方向，并覆盖桌面与移动端。

**Architecture:** 继续由 `LoginModal.vue` 负责弹窗编排、表单校验和认证事件；新增 `auth-dialog__signal` 与 `auth-dialog__panel` 两个表现层区域，右侧复用现有 Element Plus `el-tabs` / `el-form`。所有视觉调整通过组件 scoped CSS 与 `:deep` 覆盖 Element Plus 弹窗内部样式完成，不修改 Pinia、API、路由或后端。

**Tech Stack:** Vue 3 `<script setup>`、Element Plus、CSS custom properties、Node.js built-in test runner、Vite。

---

### Task 1: 建立认证页面视觉契约测试

**Files:**
- Create: `frontend/tests/auth-modal-contract.test.js`
- Test: `frontend/tests/auth-modal-contract.test.js`

- [ ] **Step 1: 写失败的结构契约测试**

创建测试并读取 `src/components/LoginModal.vue`，先锁定必须存在的结构、文案和响应式规则：

```js
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = await readFile(new URL('../src/components/LoginModal.vue', import.meta.url), 'utf8')

test('认证弹窗使用信号分栏结构与确认文案', () => {
  assert.match(source, /class="auth-dialog"/)
  assert.match(source, /class="auth-dialog__signal"/)
  assert.match(source, /class="auth-dialog__panel"/)
  assert.match(source, /把每一次登录，变成研究开始/)
  assert.match(source, /继续你的市场研究/)
  assert.match(source, /创建研究账户/)
})

test('登录与注册表单保持焦点、校验和回车行为', () => {
  assert.match(source, /ref="loginFormRef"/)
  assert.match(source, /ref="registerFormRef"/)
  assert.match(source, /@keyup\.enter="handleLogin"/)
  assert.match(source, /@keyup\.enter="handleRegister"/)
  assert.match(source, /focusFirstInvalid\(loginFormRef\)/)
  assert.match(source, /focusLoginRecoveryField\(/)
})

test('认证弹窗声明移动端单栏规则与可触控控件尺寸', () => {
  assert.match(source, /@media\s*\(max-width:\s*640px\)/)
  assert.match(source, /min-height:\s*44px/)
  assert.match(source, /label-position="top"/)
})
```

- [ ] **Step 2: 运行测试确认当前实现失败**

Run: `node --test tests/auth-modal-contract.test.js`

Expected: FAIL，原因是当前 `LoginModal.vue` 尚未包含 `auth-dialog` 结构与对应文案。

### Task 2: 重组 LoginModal 模板，保留认证逻辑

**Files:**
- Modify: `frontend/src/components/LoginModal.vue:1-111`

- [ ] **Step 1: 添加弹窗视觉壳与左侧信号区**

将现有 `<el-dialog>` 内容包裹为以下结构；保留 `v-model`、`close-on-click-modal`、`@closed` 和 `defineExpose({ open })`：

```vue
<el-dialog
  v-model="visible"
  class="auth-dialog"
  :title="activeTab === 'login' ? '登录研究工作台' : '创建研究账户'"
  width="min(760px, calc(100vw - 32px))"
  :close-on-click-modal="false"
  @closed="handleClosed"
>
  <div class="auth-dialog__shell">
    <aside class="auth-dialog__signal">
      <div class="auth-dialog__brand">
        <span class="auth-dialog__brand-mark">研</span>
        <span>股票研究台</span>
      </div>
      <div class="auth-dialog__eyebrow">Market intelligence</div>
      <h2>把每一次登录，变成研究开始。</h2>
      <p>指数、板块、个股与 AI 观察，回到同一个清晰的工作台。</p>
      <div class="auth-dialog__signal-strip" aria-label="研究工作台能力">
        <span>指数</span><span>板块</span><span>个股</span><span>AI 观察</span>
      </div>
      <p class="auth-dialog__disclaimer">数据仅供研究参考，不构成投资建议。</p>
    </aside>

    <section class="auth-dialog__panel">
      <div class="auth-dialog__panel-heading">
        <h3>{{ authHeading }}</h3>
        <p>{{ authSubheading }}</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
      </el-tabs>
    </section>
  </div>
</el-dialog>
```

- [ ] **Step 2: 调整登录与注册表单的表现层属性**

两个 `<el-form>` 都改为 `class="auth-form" label-position="top"`，移除固定 `label-width`；保留原有 `ref`、`model`、`rules`、`@keyup.enter` 和所有事件处理。每个提交按钮保留 `:loading` 与 handler，改为 `class="auth-submit"`，登录文案使用「进入研究工作台」，注册文案使用「创建研究账户」。在注册表单的确认密码字段之后追加：

```vue
<p class="auth-form__note">注册后即可同步保存你的自选与研究报告。</p>
```

- [ ] **Step 3: 添加动态标题计算属性**

将脚本的 import 改为包含 `computed`，并在 `activeTab` 定义后加入：

```js
const authHeading = computed(() => (
  activeTab.value === 'login' ? '欢迎回来' : '建立你的研究账户'
))

const authSubheading = computed(() => (
  activeTab.value === 'login'
    ? '继续你的市场研究'
    : '注册后同步保存你的自选与报告'
))
```

除上述展示文案外，不改动 `handleLogin`、`handleRegister`、`handleClosed`、`handleShowLogin` 的控制流。

### Task 3: 实现信号分栏视觉样式与响应式行为

**Files:**
- Modify: `frontend/src/components/LoginModal.vue:220-260`

- [ ] **Step 1: 添加弹窗、左右分栏和品牌区样式**

在 `<style scoped>` 中写入认证专用规则，并用 `:deep` 覆盖 Element Plus teleported dialog：

```css
.auth-dialog :deep(.el-dialog) {
  overflow: hidden;
  padding: 0;
  border: 1px solid var(--border-default);
  border-radius: 12px;
  background: var(--surface-primary);
  box-shadow: 0 22px 60px rgba(24, 33, 43, .24);
}

.auth-dialog :deep(.el-dialog__header) {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 3;
  width: 30px;
  height: 30px;
  margin: 0;
  padding: 0;
}

.auth-dialog :deep(.el-dialog__title) { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.auth-dialog :deep(.el-dialog__headerbtn) { width: 30px; height: 30px; border-radius: var(--radius-sm); }
.auth-dialog :deep(.el-dialog__body) { padding: 0; }

.auth-dialog__shell { display: grid; grid-template-columns: 44% 56%; min-height: 470px; }
.auth-dialog__signal { position: relative; overflow: hidden; padding: 38px 32px; color: #dce8ee; background: var(--surface-sidebar); }
.auth-dialog__signal::after { content: ""; position: absolute; right: -128px; bottom: -134px; width: 260px; height: 260px; border: 1px solid rgba(217, 164, 65, .42); border-radius: 50%; box-shadow: 0 0 0 28px rgba(217, 164, 65, .06), 0 0 0 56px rgba(217, 164, 65, .04); }
.auth-dialog__brand { display: flex; align-items: center; gap: 9px; color: var(--text-inverse); font-size: 14px; font-weight: 700; }
.auth-dialog__brand-mark { display: grid; place-items: center; width: 30px; height: 30px; border: 1px solid #d9a441; color: #f0c66e; font: 700 12px var(--font-family-mono); }
.auth-dialog__eyebrow { margin-top: 62px; color: var(--text-sidebar-muted); font-size: 10px; letter-spacing: .14em; text-transform: uppercase; }
.auth-dialog__signal h2 { max-width: 280px; margin: 11px 0 12px; color: var(--text-inverse); font-size: clamp(26px, 2.8vw, 32px); line-height: 1.15; letter-spacing: -.04em; }
.auth-dialog__signal > p { max-width: 260px; margin: 0; color: #aebfca; font-size: 13px; line-height: 1.7; }
.auth-dialog__signal-strip { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 28px; }
.auth-dialog__signal-strip span { padding: 4px 7px; border: 1px solid rgba(217, 164, 65, .42); color: #f0c66e; font-size: 10px; }
.auth-dialog__disclaimer { position: absolute; right: 32px; bottom: 28px; left: 32px; max-width: none !important; padding-top: 12px; border-top: 1px solid rgba(220, 232, 238, .2); color: #91a6b4 !important; font-size: 10px !important; }
```

- [ ] **Step 2: 添加表单层级、输入态和 CTA 样式**

继续在同一 `<style scoped>` 中加入：

```css
.auth-dialog__panel { display: grid; align-content: center; padding: 42px 44px 36px; background: var(--surface-primary); }
.auth-dialog__panel-heading h3 { margin: 0 0 6px; color: var(--text-primary); font-size: 24px; letter-spacing: -.02em; }
.auth-dialog__panel-heading p { margin: 0 0 24px; color: var(--text-secondary); font-size: 13px; }
.login-tabs { margin-top: 0; }
.login-tabs :deep(.el-tabs__header) { margin: 0 0 25px; }
.login-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; background-color: var(--border-subtle); }
.login-tabs :deep(.el-tabs__active-bar) { height: 2px; background-color: var(--color-primary-500); }
.login-tabs :deep(.el-tabs__item) { height: 34px; padding: 0 0 10px; margin-right: 20px; color: var(--text-tertiary); font-size: 13px; }
.login-tabs :deep(.el-tabs__item.is-active) { color: var(--color-primary-700); font-weight: 700; }
.auth-form :deep(.el-form-item) { margin-bottom: 16px; }
.auth-form :deep(.el-form-item__label) { height: auto; padding: 0 0 7px; color: var(--text-primary); font-size: 12px; font-weight: 700; line-height: 1.3; }
.auth-form :deep(.el-input__wrapper) { min-height: 44px; border: 1px solid var(--border-default); border-radius: 6px; background: var(--surface-primary); box-shadow: none; }
.auth-form :deep(.el-input__wrapper:hover) { border-color: var(--border-strong); }
.auth-form :deep(.el-input.is-focus .el-input__wrapper) { border-color: var(--color-primary-500); box-shadow: 0 0 0 3px var(--focus-ring-soft); }
.auth-form :deep(.el-form-item.is-error .el-input__wrapper) { border-color: var(--color-error-500); }
.auth-submit { width: 100%; min-height: 46px; margin-top: 3px; border: 0; border-radius: 6px; background: var(--color-primary-500); box-shadow: 0 6px 14px rgba(43, 110, 153, .18); font-size: 13px; font-weight: 700; }
.auth-submit:hover { background: var(--color-primary-600); }
.auth-form__note { margin: -3px 0 14px; color: var(--text-tertiary); font-size: 11px; line-height: 1.55; }
```

- [ ] **Step 3: 添加移动端断点与 reduced-motion 兼容**

追加以下规则，确保 640px 以下为上下结构且触控目标保持可用：

```css
@media (max-width: 640px) {
  .auth-dialog :deep(.el-dialog) { width: calc(100vw - 24px) !important; margin-top: 6vh; }
  .auth-dialog__shell { grid-template-columns: 1fr; min-height: 0; }
  .auth-dialog__signal { min-height: 172px; padding: 24px 22px 22px; }
  .auth-dialog__eyebrow { margin-top: 21px; }
  .auth-dialog__signal h2 { max-width: 300px; margin: 7px 0 0; font-size: 23px; }
  .auth-dialog__signal > p:not(.auth-dialog__disclaimer), .auth-dialog__signal-strip, .auth-dialog__disclaimer { display: none; }
  .auth-dialog__panel { padding: 26px 22px 30px; }
  .auth-dialog :deep(.el-tabs__item), .auth-dialog :deep(.el-button) { min-height: 44px; }
  .auth-dialog :deep(.el-tabs__item) { height: 44px; padding-bottom: 11px; }
}

@media (prefers-reduced-motion: reduce) {
  .auth-dialog *, .auth-dialog *::before, .auth-dialog *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
```

### Task 4: 运行测试、构建并做浏览器验收

**Files:**
- Test: `frontend/tests/auth-modal-contract.test.js`
- Test: `frontend/tests/auth-validation.test.js`

- [ ] **Step 1: 运行认证相关测试**

Run: `cd frontend && node --test tests/auth-modal-contract.test.js tests/auth-validation.test.js`

Expected: 所有测试 PASS。

- [ ] **Step 2: 构建前端**

Run: `cd frontend && npm run build`

Expected: Vite 构建成功并生成 `frontend/dist/`，无 Vue 模板或 CSS 编译错误。

- [ ] **Step 3: 启动前端并检查关键交互**

Run: `cd frontend && npm run dev -- --host 0.0.0.0`

在 `http://localhost:52764`（项目约定端口）检查：

1. 桌面宽度确认左右分栏、关闭按钮、tab 底部线、输入框和 CTA 层级。
2. 切换注册确认标题、副文案、三字段校验与确认密码规则不变。
3. 输入错误凭证确认错误提示出现且焦点回到可恢复字段。
4. 关闭弹窗重新打开确认焦点、字段值和 pending route 行为不回归。
5. 390px 左右宽度确认上下结构、无横向滚动、输入和按钮至少 44px 高。

- [ ] **Step 4: 仅提交本任务文件**

在当前已有大量用户改动的工作区中，只暂存本任务相关文件：

```bash
git add frontend/src/components/LoginModal.vue frontend/tests/auth-modal-contract.test.js docs/superpowers/plans/2026-08-30-auth-redesign.md
git commit -m "feat(auth): 重设计登录注册弹窗"
```

不要暂存或覆盖其他工作区改动。
