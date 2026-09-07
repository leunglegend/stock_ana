# 项目进度

最后更新：2026-09-06（test 分支工作区 · 供 codex / agent 交接）

> 本文件由 git 跟踪，与各 worktree 共用同一份。改动后在本分支 commit 即同步到当前工作区；合并/变基时以对应分支为准。

## 项目概览

智能股票分析平台 — Vue 3 + FastAPI + AKShare + 大模型（火山引擎 Coding Plan / Anthropic 兼容 / 现接 DeepSeek）的股票分析网站。输入代码 → 行情/K线/财务 → AI 生成分析建议。

## 当前分支拓扑（重要）

三条线并行，各自独立演进，**都未互相合并**：

| 分支 | 基线 | 状态 | 内容 |
|------|------|------|------|
| `main` | — | 已发布 | 美股复盘 `/us`（UsMarket.vue）、板块/市场多源 fallback、盘后复盘、通知、机会雷达、监控等全量功能；latest `3dcd6ce` |
| `test`（**本工作区**） | `main` 前身 baa738b | 工作区当前分支 | 领先 main 3 笔：决策报告（`3402ff2`）、美股方向 docs（`cb82751`）、auto-save 脚本（`3dd3a0e`）；**不含 main 上的美股实现**（frontend 无 UsMarket.vue） |
| `feat/tip-pay-support` | main（3dcd6ce） | 🔴 独立 worktree `us-stock` 推进中 | 点赞打赏功能，领先 main 14 笔（收款码已接真码 `9f734ae`） |
| `fix/us-sector-title-sink` | main（3dcd6ce） | 🔴 独立 worktree `us-layout-fix` 推进中 | 美股切板块整页标题下沉修复，领先 main 1 笔 `63f19a2` |

worktree 位置：`.claude/worktrees/us-stock`、`.claude/worktrees/us-layout-fix`。

## 功能完成度

### ✅ 已上线（main / test 共有基线）

#### 后端 API
| 接口 | 方法 | 路径 |
|------|------|------|
| 健康检查 | GET | `/` |
| 股票搜索 | GET | `/api/stock/search?q=` |
| 股票行情 | GET | `/api/stock/{code}` |
| K线数据 | GET | `/api/stock/{code}/kline`（日/周/月K + MA + MACD + KDJ + RSI） |
| 财务数据 | GET | `/api/stock/{code}/financial` |
| AI 个股分析 | GET | `/api/stock/{code}/analyze`（SSE 流式） |
| 行业/概念板块 | GET | `/api/board/industry`、`/api/board/concept` |
| 板块成分股 | GET | `/api/board/{type}/{name}/stocks` |
| 市场概览 | GET | `/api/board/market/summary` |
| AI 市场点评 | GET | `/api/board/market/ai-summary`（SSE） |
| 盘中监控总览 | GET | `/api/monitor/overview`（需登录） |
| 用户注册/登录/当前用户 | POST/POST/GET | `/api/auth/register` `/login` `/me` |
| 自选股分组/明细/同步 | — | `/api/watchlist/*`（需登录） |
| 复盘报告列表/详情/生成 | — | `/api/reports*` |
| 通知列表/未读/已读 | — | `/api/notifications*` |

#### 前端页面
Dashboard（`/`）、个股详情（`/stock/:code`）、自选股（`/watchlist`）、板块监控（`/board`）、复盘列表（`/reports`）、复盘详情（`/reports/:id`）、盘中监控（`/monitor`）、机会雷达（`/radar`）、搜索页（`/search`）。

### 🇺🇸 美股复盘（main 已上线，test 分支未含）
- `/us` 页面 + Dashboard 美股收盘摘要卡；3 大美股指数、11 个 GICS 板块等权口径、板块内领涨领跌成分、AI 一句话主线（SSE）
- 文件：`frontend/src/views/UsMarket.vue`（main 才有）；后端美股数据链路（AKShare 新浪美股 + V8 预热）
- 演进：PR#1 装配 → PR#3 V8 预热修复多线程崩溃 → PR#4 版式对齐；版本发布流程固化 PR#2

### 🟡 test 分支新推进（未合 main）
- **AI 决策报告**：后端 `GET /api/stock/{code}/decision-report`（`3402ff2`，已合入 test）
  - 前端个股页「决策报告」标签，切到才懒加载；`DecisionReport.vue` 组件 + 契约测试
  - 结构化 JSON 输出显式 `thinking={"type":"disabled"}`（DeepSeek 等推理模型适配）
  - 全链路同步 AKShare 调用改 `run_in_threadpool`（消除事件循环阻塞/超时）；日K/财务加短 TTL 缓存与请求锁
  - 测试：后端 `test_decision_report.py`、前端 `decision-report-contract.test.js`；全绿

## 在办事项

- [ ] `feat/tip-pay-support`（us-stock worktree）：点赞打赏——收款码已接真码，仍有收尾（存根/契约/合规文案）
- [ ] `fix/us-sector-title-sink`（us-layout-fix worktree）：美股切板块标题下沉/回弹修复，query 级导航禁滚屏
- [ ] 决策报告待合并 main（test 领先 main 3 笔未合）

## 待办 / 规划

- [ ] **美股方向二期**：`direction1` plan(2026-09-03-us-stock-direction1.md)实为美股复盘功能的实施蓝图,其目标(美股复盘 /us + Dashboard 摘要卡)已在 **main 上线**(PR#1 ec06a80, 2026-09-04);文档状态行未回填,勿当"未开始"。二期边界(个股新闻/美股个股详情等)另案
- [ ] 登录注册页 UI 重设计（`docs(auth)` 规格已提交：f6c9c61 / 1f0995b，界面未做）
- [ ] 打赏 QR 素材（`frontend/src/assets/{alipay,wechat}-qr.jpg`）待 tip-pay 分支接线，当前 test 工作区无引用

## 启动命令（端口已统一 52764，旧文档 8000 作废）

```bash
# 后端
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 52764

# 前端
cd frontend && npm run dev    # http://localhost:5173，/api 代理到 52764
```

## 测试

```bash
# 后端（用 venv 直跑，避免环境差异）
cd backend && venv/bin/python -m pytest tests/ -q        # 当前 101 passed + 5 subtests

# 前端契约测试（纯 node，不依赖 vite）
cd frontend && node --test tests/*.test.js               # 当前 198 passed
```

## 已知问题 & 坑（重要）

1. **AI 配置被 shell 环境变量劫持**：本机 shell 全局设了 `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic` + `ANTHROPIC_AUTH_TOKEN`（供 Claude Code 走 DeepSeek）。后端 `config.py` 用 `ARK_*` 优先、否则回退 `ANTHROPIC_*` → **实际连 DeepSeek 而非 README/.env.example 的火山引擎**。排查 AI 接口失败先 `env | grep -iE "ARK_|ANTHROPIC"`。要换供应商在 `backend/.env` 显式写 `ARK_API_KEY`/`ARK_BASE_URL`/`ARK_MODEL` 覆盖。
2. **DeepSeek 是推理模型**：结构化输出（决策报告）必须显式 `thinking={"type":"disabled"}`，否则 max_tokens 全耗在 ThinkingBlock → TextBlock 空 →「不是有效 JSON」。诊断打印 `text_len=0`。
3. **东财接口网络问题**：`*_em` 接口在部分网络 Connection reset，已做多源 fallback（东财 → 同花顺 → 旧缓存）。
4. **async 路由不得直接同步调 AKShare**：会阻塞事件循环导致全部 /api 超时，必须 `run_in_threadpool`（板块成分股路由已补测，回归测试 test_board_route_not_blocking.py 守护）。
5. **内存管理**：macOS low-memory 会杀后台任务（vite ~20MB、uvicorn ~18MB）。多 worktree 同时跑服务易被杀，优先只跑一条线的标准端口。
6. 定时任务仅按周一到周五，不判节假日；JWT token 存 localStorage 为轻量方案。
7. `decision-brief.preview.html` 是本地预览衍生品，不入库；`.claude/worktrees/` 与 `settings.local.json` 已被 .gitignore 忽略。

## 文件结构速查

```
backend/app/
├── main.py / config.py / database.py / dependencies.py
├── models/           # SQLAlchemy ORM（user/watchlist/report/notification/schemas.py）
├── routes/           # stock / board / monitor / auth / watchlist / report / notification
├── services/         # stock_data / board_data / market_data / ai_analyst / monitor_service
│                     # report_service / notification_service / auth_service
│                     # signal_rules / data_cache / scheduler / sse
└── tests/

frontend/src/
├── views/            # Dashboard / StockDetail / Watchlist / BoardMonitor / Reports
│                     # ReportDetail / Monitor / OpportunityRadar / Search
├── components/       # base / app / stock / board / dashboard / monitor / radar / reports / watchlist
├── api/  store/  router/  composables/  styles/  utils/
frontend/tests/       # *.test.js 契约测试（node --test 直跑）
docs/design-rounds/   # 设计决策轮方案 + decision-brief
docs/superpowers/plans/  # 历次功能实施计划
```
