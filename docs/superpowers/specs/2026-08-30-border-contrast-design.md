# 研究台页面边框可读性增强设计

## 目标

在不改变业务逻辑、页面布局、信息架构、主题入口和圆角/阴影语言的前提下，采用用户确认的 B「平衡增强」方案，让研究台的主要工作区边界更容易被快速识别。

## 设计原则

- 外框清晰、内部分隔克制：主要工作区和卡片外框使用 `--border-default`，标题、数据行和分组分隔使用更轻的 `--border-subtle`。
- 主题一致：Ocean、Jade、Charcoal 都提供对应的冷灰、灰绿、暖灰边框层级，保持相同的语义对比关系。
- 组件复用 Token：不在页面组件中新增固定颜色；共享组件和 Element Plus 适配层继续消费语义 Token。
- 不用阴影替代边界：普通研究台表面继续保持无阴影，只有弹层沿用现有提升阴影。

## 改动范围

### Token 层

调整 `frontend/src/styles/tokens.css` 中三套主题的 `--border-subtle`、`--border-default`、`--border-strong`，使默认外框与内部线之间形成稳定、可读的层级。颜色需要满足浅色页面上的可辨识度，并保持文字与交互焦点的既有对比度。

### 共享表面与组件

- `frontend/src/style.css`：工作台表面外框使用 `--border-default`；页面头部和工具栏继续使用 `--border-subtle`。
- `frontend/src/components/base/SectionPanel.vue`、`AppCard.vue`：面板外框使用默认边框，头尾分隔使用次级边框。
- `frontend/src/styles/element-plus.css`：统一 Element Plus 卡片、表格、输入/选择器、Tab 和分页的边框来源，避免组件自带浅色线条覆盖 Token。

不修改页面数据、路由、响应式断点、交互事件及 API 合约。

## 验收标准

1. 主要页面的工作区/卡片外框比当前更易定位，内部数据行仍保持轻量。
2. 三套主题均保持同一边框语义层级，无组件级 raw color 回归。
3. 键盘焦点、hover、表格选中态和弹层阴影不被削弱。
4. 前端样式契约测试与生产构建通过，`git diff --check` 无错误。
5. 在 `http://localhost:52766` 的对比页复核后，视觉效果符合 B 方案：清晰但不显得厚重。

## 风险与回退

若某个页面因组合边框显得过重，只回退该页面内部线条到 `--border-subtle`，不新增局部颜色；如主题对比度不均，则仅调整对应主题 Token。
