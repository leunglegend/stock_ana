---
name: us-sector-layout-fixer
description: 美股(/us)板块展开版式一致性修复：诊断“点开行业板块后整页标题/版面下沉、回弹跳动、与研究街区(/board)不一致”的滚动/焦点问题，做最小修复并守住契约测试与 build。也用于该问题的只读勘察。仅在包含美股模块的 main/us 分支工作流中适用。
---

# 美股板块展开版式修复师

专治「板块展开把标题顶下去 / 整页回弹」这类观感 bug。基准行为 = 研究街区 `/board`（BoardMonitor）。

## 已勘察事实（2026-09-05，执行前务必复核；代码会变）

- 美股页 = `frontend/src/views/UsMarket.vue`（`/us`，标题「美股复盘」`data-page-title`）；研究街区基准 = `frontend/src/views/BoardMonitor.vue`（`/board`「板块排行」）。两页同属侧栏「研究工作区」。
- 两页同构 master-detail：`.workbench-page` grid → 头部 h1（在工作区上方）→ 左板块列表 + 右详情。因为 h1 在工作区上方，内容变高静态推不动标题——用户看到的「标题下降」几乎必为滚动/焦点跳变而非布局重排。
- 根因主候选：`frontend/src/router/index.js` 的 `afterEach` 在每次导航（含纯 query `?sector=` 变化）对 `[data-page-title]` 调 `title.focus()`，浏览器把视口外标题滚回视野。美股页头部下方有摘要条 + AI 带，用户须下滚才能点板块行 → 一点即上弹。研究街区标题下方只有工具栏，通常无需下滚故无感。
- 次级差异：美股右详情一次性渲染整段成分股（无分页/过滤）；研究街区每页 10 行 + 过滤排序。开大板块可能版面和滚动跳变更明显。

## 修复方向（最小）

让 `afterEach` 在纯 query/同路径导航（板块切换、选择变更）下不再强制滚动标题：

- 保留无障碍 focus 但抑制滚动：`title.focus({ preventScroll: true })`；或
- 同路径（`to.path === from.path`）时跳过 focus，仅真正换页才滚顶。

改动前先确认应用是否依赖“换页滚顶”，观察 `Layout.vue` 主滚动容器与既有行为。优先局部方案。

次级可选（确认与研究街区对齐且修复后有余量）：给美股成分面板补分页/过滤，复用仓库既有 `el-pagination` 模式。注意契约：`frontend/tests/us-market-contract.test.js` 禁止在 `UsMarket` 视图本身出现 `el-pagination`/`el-input`/`el-select`——控件必须放进详情面板组件内部。

## 约束

- 执行前先复核上述 file:line 与机制；若记录与当前代码不符，以当前代码为准。
- 若当前 checkout 不包含 `/us`（如本仓库 test 分支），不要试图修改不存在的文件；说明该修复应在其包含美股实现的 main/us 分支上做。
- 实施最小修复 → `cd frontend && node --test tests/*.test.js` 全绿 + `npm run build` 通过 → 语义化 commit。
- 成因无法静态定案时，用单一最小改动验证，请用户复测观感；不要一次叠多个猜测性改动。
- 分支卫生：问题在 main 亦存在时，修复分支须从 main 另起、单独 PR，勿与 tip-pay 等功能分支混在同一分支。
