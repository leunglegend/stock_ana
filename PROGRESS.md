# 项目进度

最后更新：2026-08-25

## 项目概览

智能股票分析平台 — 基于 Vue 3 + FastAPI + AKShare + 大模型的股票分析网站。

## 功能完成度

### ✅ 已完成

#### 后端 API
| 接口 | 方法 | 路径 | 状态 | 说明 |
|------|------|------|------|------|
| 健康检查 | GET | `/` | ✅ | |
| 股票搜索 | GET | `/api/stock/search?q=` | ✅ | 代码/名称模糊搜索，本地缓存 1h |
| 股票行情 | GET | `/api/stock/{code}` | ✅ | K线降级兜底，稳定可靠 |
| K线数据 | GET | `/api/stock/{code}/kline` | ✅ | 日/周/月K + MA5/10/20 + MACD + KDJ + RSI(6/12/24) |
| 财务数据 | GET | `/api/stock/{code}/financial` | ✅ | PE/PB/总市值/ROE/净利润/营收/毛利率/净利率 |
| AI 个股分析 | GET | `/api/stock/{code}/analyze` | ✅ | SSE 流式输出 |
| 行业板块 | GET | `/api/board/industry` | ✅ | 多数据源 fallback，90 个板块 |
| 概念板块 | GET | `/api/board/concept` | ✅ | 多数据源 fallback |
| 板块成分股 | GET | `/api/board/{type}/{name}/stocks` | ✅ | 行业/概念板块成分股列表 |
| 市场概览 | GET | `/api/board/market/summary` | ✅ | 三大指数 + 涨跌家数 + 涨跌停 + 成交额 |
| AI 市场点评 | GET | `/api/board/market/ai-summary` | ✅ | SSE 流式输出 |
| 用户注册 | POST | `/api/auth/register` | ✅ | 用户名+密码 |
| 用户登录 | POST | `/api/auth/login` | ✅ | 返回 JWT token |
| 当前用户 | GET | `/api/auth/me` | ✅ | |
| 自选股分组列表 | GET | `/api/watchlist/groups` | ✅ | 需登录，含分组下的股票 |
| 新建/更新/删除分组 | POST/PUT/DELETE | `/api/watchlist/groups` | ✅ | |
| 添加/更新/删除自选股 | POST/PUT/DELETE | `/api/watchlist/items` | ✅ | |
| 批量同步自选股 | POST | `/api/watchlist/sync` | ✅ | 支持 replace 模式 |
| 复盘报告列表 | GET | `/api/reports` | ✅ | 分页 |
| 复盘报告详情 | GET | `/api/reports/{id}` | ✅ | 含个股分析 |
| 手动生成复盘 | POST | `/api/reports/generate` | ✅ | 后台异步执行 |
| 通知列表 | GET | `/api/notifications` | ✅ | 分页 + 未读筛选 |
| 通知未读数 | GET | `/api/notifications/unread-count` | ✅ | |
| 标记已读 | PUT | `/api/notifications/{id}/read` | ✅ | |
| 全部已读 | PUT | `/api/notifications/read-all` | ✅ | |

#### 前端页面
| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 首页/市场概览 | `/` | ✅ | 三大指数 + 市场情绪 + 热门板块 + AI 点评 |
| 个股详情 | `/stock/:code` | ✅ | 行情栏 + K线图 + 财务 + AI 分析 |
| 自选股 | `/watchlist` | ✅ | 分组管理 + 成本 + 盈亏计算 + 云端同步 |
| 板块监控 | `/board` | ✅ | 行业/概念 Tab + 板块详情抽屉 |
| 复盘报告列表 | `/reports` | ✅ | 历史报告列表 + 手动生成 |
| 复盘报告详情 | `/reports/:id` | ✅ | 市场总览 + 关注重点 + 个股分析 + 风险提示 |

#### 前端组件
| 组件 | 状态 | 说明 |
|------|------|------|
| 登录/注册弹窗 | ✅ | 用户名 + 密码，Tab 切换 |
| 消息铃铛 | ✅ | 未读数红点 + 下拉列表 + 全部已读 |
| 用户状态侧边栏 | ✅ | 未登录显示登录按钮，已登录显示用户名+退出 |

#### 技术指标（K线副图）
- 成交量（柱状）
- MACD（DIF/DEA/MACD柱）
- KDJ（K/D/J 三线）
- RSI（6/12/24 日）

#### 系统能力
- **用户系统**：用户名 + 密码 + JWT 鉴权
- **自选股云端同步**：本地/云端双模式，首次登录自动提示同步
- **盘后 AI 复盘**：APScheduler 定时任务，交易日 15:30 自动生成
- **消息中心**：站内信通知，60s 轮询未读数

### 🔧 架构特性
- **多数据源 fallback**：东财 → 同花顺 → 旧缓存，网络波动自动降级
- **内存缓存 + 定时刷新**：板块 2min、市场概览 1min，首次同步加载
- **AKShare 懒加载**：未安装也能启动，使用时才 import
- **重试机制**：`@_retry` 装饰器，指数退避
- **CORS 配置**：支持 localhost:5173
- **SQLite 数据库**：SQLAlchemy 2.x ORM，轻量零配置
- **APScheduler 定时任务**：BackgroundScheduler，Cron 表达式可配置
- **AI JSON 解析容错**：自动提取 JSON 内容，兼容各种 AI 返回格式

## 文件结构速查

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口 + 启动预加载 + scheduler
│   ├── config.py            # 配置（含数据库/JWT/定时任务）
│   ├── database.py          # SQLAlchemy 引擎 + 会话 + Base
│   ├── dependencies.py      # get_current_user 等依赖注入
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── user.py          # 用户
│   │   ├── watchlist.py     # 自选股（分组+明细）
│   │   ├── report.py        # 复盘报告（日报+个股分析）
│   │   └── notification.py  # 通知消息
│   ├── schemas/             # Pydantic 数据模型
│   │   ├── auth.py
│   │   ├── watchlist.py
│   │   ├── report.py
│   │   └── notification.py
│   ├── routes/
│   │   ├── auth.py          # 认证 API
│   │   ├── stock.py         # 股票相关 API
│   │   ├── board.py         # 板块 + 市场 API
│   │   ├── watchlist.py     # 自选股 API
│   │   ├── report.py        # 复盘报告 API
│   │   └── notification.py  # 通知 API
│   └── services/
│       ├── stock_data.py    # 股票数据 + 技术指标计算
│       ├── board_data.py    # 板块数据（多源 fallback）
│       ├── market_data.py   # 市场概览（指数+涨跌统计+涨跌停）
│       ├── ai_analyst.py    # AI 分析（个股/市场/盘后复盘）
│       ├── auth_service.py  # 认证服务（密码哈希/JWT）
│       ├── watchlist_service.py  # 自选股服务
│       ├── report_service.py     # 复盘报告服务
│       ├── notification_service.py  # 通知服务
│       ├── scheduler.py     # APScheduler 定时任务
│       └── data_cache.py    # 缓存管理 + 定时刷新
├── requirements.txt
└── .env.example

frontend/
├── src/
│   ├── views/               # Dashboard / StockDetail / Watchlist / BoardMonitor / Reports / ReportDetail
│   ├── components/          # StockSearch / StockInfo / KLineChart / FinancialCard / AiAdvice / Layout
│   │                        # / LoginModal / NotificationBell / GlobalSearch
│   ├── api/                 # http.js (通用axios) + stock.js + auth.js + watchlist.js + report.js + notification.js
│   ├── store/               # index.js (自选股 store) + user.js (用户 store)
│   └── router/index.js      # 路由 + 登录守卫
└── vite.config.js           # /api 代理到 8000 + @ 别名
```

## 已知问题 & 注意事项

1. **东财接口网络问题**：`*_em` 后缀的接口在某些网络环境可能 Connection reset，代码已做多源 fallback
2. **涨跌家数精度**：优先全量行情统计，失败时用行业板块估算（会有偏差）
3. **AI 配置**：需要 `ARK_API_KEY` + `ARK_MODEL`，未配置时显示友好提示
4. **非交易时段**：实时行情可能延迟，K线数据作为降级方案更稳定
5. **自选股存储**：支持 localStorage（游客）+ 服务端（登录用户）双模式
6. **bcrypt 版本警告**：passlib 与 bcrypt 5.x 不兼容，已降级到 4.x，有 warning 但不影响功能
7. **定时任务节假日**：仅按周一到周五调度，不判断法定节假日
8. **Token 存储**：JWT token 存在 localStorage，轻量方案；生产环境建议使用 HTTP-only Cookie

## 启动命令

```bash
# 后端
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm run dev    # http://localhost:5173
```

## 环境变量（新增）

```bash
# 数据库
DATABASE_URL=sqlite:///./stock_analyzer.db

# JWT（必须配置）
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# 定时任务
SCHEDULER_ENABLED=true
DAILY_REPORT_CRON=30 15 * * 1-5
```

## 后续可做

- [ ] 邮箱验证 / 找回密码
- [ ] K线更多指标（BOLL、OBV、WR 等）
- [ ] 多股对比功能
- [ ] 选股器（按财务/技术指标筛选）
- [ ] 回测功能
- [ ] 邮件推送 / Webhook 推送
- [ ] 报告导出（PDF/图片）
- [ ] 节假日判断（更精准的定时任务）
