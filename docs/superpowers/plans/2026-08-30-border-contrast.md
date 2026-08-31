# 研究台页面边框可读性增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按用户确认的 B「平衡增强」方案提升三套研究台皮肤的页面和工作区边框可读性。

**Architecture:** 保持现有语义 Token 架构，集中调整三套主题的 `--border-subtle`、`--border-default`、`--border-strong`，让共享面板和 Element Plus 适配层自动获得一致的边框层级。页面组件不新增固定颜色、不改变布局和业务逻辑。

**Tech Stack:** Vue 3、Element Plus、CSS custom properties、Node.js built-in test runner、Vite。

---

### Task 1: 为边框层级补充回归契约

**Files:**
- Modify: `frontend/tests/new-feature-style-contract.test.js`
- Test: `frontend/tests/new-feature-style-contract.test.js`

- [x] **Step 1: 添加颜色解析和边框层级断言**

在现有 `new-feature-style-contract.test.js` 的 Token 测试附近加入以下辅助函数与测试。测试直接读取三套主题块，要求每套主题的 subtle、default、strong 使用批准的 B 方案颜色，并且默认边框比内部线更暗：

```js
function extractHex(block, token) {
  return block.match(new RegExp(`${token}:\\s*(#[0-9a-f]{6});`, 'i'))?.[1].toLowerCase()
}

function relativeLuminance(hex) {
  const channels = [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16) / 255)
  const linear = channels.map((channel) => (
    channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
  ))
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
}

test('三套主题使用平衡增强边框层级', () => {
  const expected = {
    ocean: { subtle: '#d2dce4', default: '#aebdca', strong: '#7f95a8' },
    jade: { subtle: '#cadbd3', default: '#a9bfb4', strong: '#789486' },
    charcoal: { subtle: '#d8d1c7', default: '#b8aea1', strong: '#918477' },
  }

  for (const [theme, colors] of Object.entries(expected)) {
    const block = theme === 'ocean'
      ? tokensSource.match(/:root\\s*\\{[\\s\\S]*?\\n\\}/)?.[0] || ''
      : tokensSource.match(new RegExp(`:root\\[data-theme=['"]${theme}['"]\\]\\s*\\{[\\s\\S]*?\\n\\}`))?.[0] || ''
    const subtle = extractHex(block, '--border-subtle')
    const normal = extractHex(block, '--border-default')
    const strong = extractHex(block, '--border-strong')
    assert.deepEqual({ subtle, default: normal, strong }, colors, `${theme} 边框 Token 不符合 B 方案`)
    assert.ok(relativeLuminance(normal) < relativeLuminance(subtle), `${theme} 默认边框应比内部线更深`)
    assert.ok(relativeLuminance(strong) < relativeLuminance(normal), `${theme} 强边框应比默认边框更深`)
  }
})
```

- [x] **Step 2: 运行定向测试，确认新增契约先失败**

Run: `cd frontend && node --test tests/new-feature-style-contract.test.js`

Expected: 新增的 `三套主题使用平衡增强边框层级` 失败，提示当前 Token 与 B 方案颜色不一致；其余既有测试保持通过。

### Task 2: 调整共享边框 Token 与组件消费

**Files:**
- Modify: `frontend/src/styles/tokens.css:251-317`
- Modify: `frontend/src/styles/element-plus.css:11-119`
- Modify: `frontend/src/components/base/SectionPanel.vue:31-58`
- Modify: `frontend/src/components/base/AppCard.vue:43-75`

- [x] **Step 1: 写入三套主题的 B 方案颜色**

将 `frontend/src/styles/tokens.css` 中三套主题的边框值替换为：

```css
/* Ocean */
--border-subtle: #d2dce4;
--border-default: #aebdca;
--border-strong: #7f95a8;

/* Jade */
--border-subtle: #cadbd3;
--border-default: #a9bfb4;
--border-strong: #789486;

/* Charcoal */
--border-subtle: #d8d1c7;
--border-default: #b8aea1;
--border-strong: #918477;
```

保留 `--border` 对 `--border-default` 的别名以及 focus、state、chart 等其他语义 Token。

- [x] **Step 2: 统一共享组件和 Element Plus 的外框/内线层级**

确认以下规则存在且只消费语义 Token；若现有声明已满足则不重复改写：

```css
/* SectionPanel.vue / AppCard.vue */
.section-panel,
.app-card {
  border: 1px solid var(--border-default);
}

.section-panel__header,
.section-panel__footer,
.app-card__header,
.app-card__footer {
  border-color: var(--border-subtle);
}

/* element-plus.css */
.el-input__wrapper,
.el-select__wrapper {
  box-shadow: 0 0 0 1px var(--border-default) inset;
}

.el-table {
  --el-table-border-color: var(--border-subtle);
  border: 1px solid var(--border-default);
}
```

若分页控件仍无可见边界，只为 `.el-pagination button, .el-pager li` 增加 `border: 1px solid var(--border-subtle)`，不增加阴影或固定颜色。

- [x] **Step 3: 运行定向测试，确认契约通过**

Run: `cd frontend && node --test tests/new-feature-style-contract.test.js tests/theme.test.js`

Expected: 所有列出的前端契约测试通过。

### Task 3: 完成构建与视觉复核

**Files:**
- Modify: `frontend/.superpowers/brainstorm/*/content/border-contrast-v2.html` (visual companion only, if a final comparison screen is needed)

- [x] **Step 1: 运行前端完整测试与生产构建**

Run: `cd frontend && node --test tests/*.test.js && npm run build`

Expected: Node 测试全部通过；Vite 构建成功，若出现既有 chunk 大小提示仅记录不作为失败。

- [x] **Step 2: 检查差异格式与未定义 Token**

Run: `git diff --check && rg -n "--border-(subtle|default|strong)" frontend/src/styles/tokens.css frontend/src/styles/element-plus.css frontend/src/components/base/SectionPanel.vue frontend/src/components/base/AppCard.vue`

Expected: `git diff --check` 无输出；四个目标文件均只引用已定义的边框 Token。

- [x] **Step 3: 在视觉伴侣中复核 B 方案**

打开 `http://localhost:52766`，确认工作区外框比 A 更容易定位，数据行没有达到 C 的厚重感；如需调整，只改对应主题 Token，不改页面结构。
