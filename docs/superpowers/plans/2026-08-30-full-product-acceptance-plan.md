# 全产品功能验收与交互修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成生产环境全功能验收，修复功能错误和有证据支撑的交互问题。

**Architecture:** 使用 API 契约脚本验证后端业务和权限边界，使用 Puppeteer 验证桌面/移动端真实任务流。缺陷按 TDD 在所属模块局部修复，并复用现有工作台设计系统。

**Tech Stack:** FastAPI、SQLAlchemy、Vue 3、Pinia、Element Plus、Vite、Node test runner、Puppeteer

---

### Task 1: 建立完整验收基线

**Files:**
- Read: `README.md`
- Read: `frontend/src/router/index.js`
- Read: `backend/app/routes/*.py`
- Create only if reusable: `frontend/tests/*-contract.test.js`
- Create only if reusable: `backend/tests/test_*.py`

- [x] 枚举路由、接口、鉴权和主要任务流。
- [x] 运行现有前后端测试与生产构建。
- [x] 记录已有警告和工作区改动，避免覆盖并行修改。

### Task 2: 验证账号与鉴权闭环

**Files:**
- Modify when a defect is proven: `backend/app/routes/auth.py`
- Modify when a defect is proven: `frontend/src/components/LoginModal.vue`
- Modify when a defect is proven: `frontend/src/store/user.js`
- Modify when a defect is proven: `frontend/src/router/index.js`

- [x] 创建唯一临时账号，验证重复注册、错误密码、登录、`/auth/me` 和退出。
- [x] 用 Chromium 验证受保护路由触发登录、登录后返回目标页、焦点和错误恢复。
- [x] 对可复现缺陷执行 RED -> GREEN -> 回归。

### Task 3: 验证自选股完整 CRUD

**Files:**
- Modify when a defect is proven: `backend/app/routes/watchlist.py`
- Modify when a defect is proven: `backend/app/services/watchlist_service.py`
- Modify when a defect is proven: `frontend/src/views/Watchlist.vue`
- Modify when a defect is proven: `frontend/src/store/index.js`

- [x] 验证分组新增、改名、股票新增、成本/备注更新、移动、删除和同步。
- [x] 验证重复项、无效分组、越权 ID 和空状态。
- [x] 验证桌面表格与移动列表操作反馈、确认和触控尺寸。

### Task 4: 验证市场研究功能

**Files:**
- Modify only when defects are proven: `frontend/src/views/*.vue`
- Modify only when defects are proven: `frontend/src/components/**/*.vue`
- Modify only when defects are proven: `backend/app/routes/stock.py`
- Modify only when defects are proven: `backend/app/routes/board.py`

- [x] 验证首页、板块筛选/排序/分页/详情、搜索/最近记录/分页。
- [x] 验证股票行情、K 线周期、财务、加入自选和 AI SSE 状态。
- [x] 在 1440、1024、768、390、360 视口检查布局、焦点、缩放和主题。

### Task 5: 验证报告与通知闭环

**Files:**
- Modify when a defect is proven: `backend/app/routes/report.py`
- Modify when a defect is proven: `backend/app/routes/notification.py`
- Modify when a defect is proven: `frontend/src/views/Reports.vue`
- Modify when a defect is proven: `frontend/src/views/ReportDetail.vue`
- Modify when a defect is proven: `frontend/src/components/NotificationBell.vue`

- [x] 验证报告列表、生成幂等性、轮询、详情和无效 ID。
- [x] 验证通知分页、未读数、单条已读和全部已读。
- [x] AI 或市场关闭时验证明确、可恢复且不误导的降级状态。

### Task 6: 清理与最终验证

**Files:**
- Test: `frontend/tests/*.test.js`
- Test: `backend/tests/test_*.py`

- [x] 通过应用接口清理临时自选数据，并清理全部 `qa_*` 临时账号及关联数据。
- [x] 运行全量前端测试、后端测试、生产构建和 `git diff --check`。
- [x] 重跑桌面/移动主任务链，检查生产服务、端口、缓存头和错误日志。
- [x] 汇总修复、验证证据、外部数据源风险和未执行项。

> 不执行 commit、push、数据库 schema 修改或依赖升级，除非用户另行授权。
