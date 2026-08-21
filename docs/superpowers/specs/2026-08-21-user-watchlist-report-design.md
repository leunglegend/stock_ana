# 设计规格：用户系统 + 自选股持久化 + 盘后 AI 复盘 + 消息中心

**日期**：2026-08-21
**状态**：待用户评审

---

## 1. 背景与目标

当前股票分析平台是纯前端数据架构：自选股存在 localStorage，没有用户系统，没有后端持久化，AI 分析只能实时调用。

本次迭代引入四个子系统：

1. **用户系统**：用户名 + 密码注册登录，JWT 鉴权
2. **自选股服务端持久化**：用户自选股数据存后端数据库，支持多端同步
3. **盘后 AI 自动复盘**：交易日收盘后定时生成自选股复盘报告
4. **消息中心（站内信）**：复盘完成通知 + 系统通知

## 2. 技术选型

| 类别 | 选型 | 理由 |
|------|------|------|
| 数据库 | SQLite + SQLAlchemy 2.x | 轻量化，零配置，个人/小团队够用；SQLAlchemy 做抽象层未来可平滑迁移 |
| ORM | SQLAlchemy（同步） | 项目已有同步风格代码，保持一致，避免异步复杂度 |
| 密码加密 | passlib[bcrypt] | Python 生态标准方案 |
| JWT | python-jose[cryptography] | 成熟稳定，FastAPI 生态推荐 |
| 定时任务 | APScheduler | 轻量 Cron 调度，进程内运行，无需额外中间件 |
| 前端状态 | Pinia（改造现有 store） | 已有 Pinia，扩展即可 |

## 3. 数据库设计

### 3.1 users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK, autoincrement | 用户 ID |
| username | String(50), unique, not null | 用户名（登录账号） |
| password_hash | String(255), not null | bcrypt 哈希后的密码 |
| created_at | DateTime | 注册时间 |
| last_login_at | DateTime | 最后登录时间 |

### 3.2 watchlist_groups（自选股分组表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 分组 ID |
| user_id | Integer, FK(users.id), not null | 所属用户 |
| name | String(50), not null | 分组名称 |
| sort_order | Integer, default 0 | 排序 |
| created_at | DateTime | 创建时间 |

索引：`(user_id, sort_order)`

### 3.3 watchlist_items（自选股明细表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 记录 ID |
| group_id | Integer, FK(watchlist_groups.id), not null | 所属分组 |
| stock_code | String(10), not null | 股票代码 |
| stock_name | String(20), not null | 股票名称 |
| cost | Float, default 0 | 成本价 |
| remark | String(200), default '' | 备注 |
| sort_order | Integer, default 0 | 排序 |
| created_at | DateTime | 添加时间 |

索引：`(group_id, sort_order)`

### 3.4 daily_reports（每日复盘总表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 报告 ID |
| user_id | Integer, FK(users.id), not null | 所属用户 |
| report_date | Date, not null | 报告日期 |
| market_summary | Text | 市场总览（AI 生成） |
| highlights | JSON | 关注重点（数组，每项含 stock_code, stock_name, reason） |
| risk_notes | Text | 风险提示 |
| status | String(20), default 'pending' | pending / generating / completed / failed |
| stock_count | Integer, default 0 | 覆盖股票数 |
| error_msg | String(500) | 失败原因 |
| created_at | DateTime | 创建时间 |
| completed_at | DateTime | 完成时间 |

索引：`(user_id, report_date DESC)`，唯一约束 `(user_id, report_date)`

### 3.5 stock_reports（个股分析表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 分析 ID |
| daily_report_id | Integer, FK(daily_reports.id), not null | 关联日报 |
| stock_code | String(10), not null | 股票代码 |
| stock_name | String(20), not null | 股票名称 |
| change_pct | Float | 当日涨跌幅（%） |
| close_price | Float | 收盘价 |
| analysis_text | Text | AI 分析文本（Markdown） |
| summary | String(500) | 一句话摘要 |
| created_at | DateTime | 创建时间 |

索引：`(daily_report_id)`

### 3.6 notifications（通知表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 通知 ID |
| user_id | Integer, FK(users.id), not null | 所属用户 |
| title | String(100), not null | 标题 |
| content | String(500) | 内容摘要 |
| type | String(20), default 'system' | report / system |
| ref_id | Integer | 关联 ID（如 report_id） |
| is_read | Boolean, default false | 是否已读 |
| created_at | DateTime | 创建时间 |

索引：`(user_id, is_read, created_at DESC)`

## 4. 后端 API 设计

### 4.1 认证模块 `/api/auth`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/register` | 否 | 注册：{username, password} → {user_id, username} |
| POST | `/login` | 否 | 登录：{username, password} → {access_token, token_type, user} |
| GET | `/me` | 是 | 获取当前用户信息 |

- JWT payload：`{sub: user_id, exp: issued_at + 24h}`
- Header：`Authorization: Bearer <token>`

### 4.2 自选股模块 `/api/watchlist`

所有接口需登录。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/groups` | 获取所有分组及分组下的股票 |
| POST | `/groups` | 新建分组：{name} |
| PUT | `/groups/{id}` | 重命名分组：{name} |
| DELETE | `/groups/{id}` | 删除分组 |
| POST | `/items` | 添加股票：{group_id, stock_code, stock_name, cost?, remark?} |
| PUT | `/items/{id}` | 更新股票：{cost?, remark?} |
| DELETE | `/items/{id}` | 删除股票 |
| POST | `/sync` | 批量同步（导入 localStorage 数据）：{groups: [...]} |

### 4.3 复盘模块 `/api/reports`

所有接口需登录。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 报告列表（分页，?page=1&page_size=20） |
| GET | `/{id}` | 报告详情（含个股分析列表） |
| POST | `/generate` | 手动触发生成今日报告（调试/补跑用） |
| POST | `/generate/{date}` | 手动生成指定日期报告 |

### 4.4 通知模块 `/api/notifications`

所有接口需登录。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 通知列表（?page=1&page_size=20&unread_only=false） |
| GET | `/unread-count` | 未读数量 |
| PUT | `/{id}/read` | 标记已读 |
| PUT | `/read-all` | 全部已读 |

## 5. 盘后复盘定时任务设计

### 5.1 调度配置
- 框架：APScheduler BlockingScheduler（集成到 FastAPI 启动事件）
- Cron：`30 15 * * 1-5`（周一至周五 15:30）
- 时区：Asia/Shanghai

### 5.2 生成流程

```
15:30 触发
  ↓
查询所有有自选股的用户（去重）
  ↓
对每个用户，并发度控制（串行/限并发 2）：
  ├─ 拉取用户所有自选股代码
  ├─ 创建 daily_report 记录（status=pending）
  ├─ 拉取当日市场概览数据（指数、涨跌家数、板块）
  ├─ 逐只股票拉取：当日行情 + 近30日K线
  ├─ 调用 AI 生成市场总览 + 关注重点 + 风险提示
  ├─ 逐只股票调用 AI 生成个股分析
  ├─ 所有 stock_reports 入库
  ├─ 更新 daily_report（status=completed, 填充内容）
  └─ 生成一条 notification（type=report）
```

### 5.3 AI Prompt 设计（盘后版）

在现有 `ai_analyst.py` 基础上新增两个函数：

- `generate_daily_report(user_stocks_data, market_data)` → 生成整体复盘
- `generate_stock_daily_analysis(stock_code, stock_data)` → 生成个股日分析（更聚焦当日表现、短期走势，300-500 字）

### 5.4 失败处理
- 单只股票 AI 调用失败 → 跳过该股票，记录日志，不影响整体
- 整体生成失败 → status=failed，记录 error_msg，不发通知
- 支持手动补跑（`POST /api/reports/generate/{date}`）

## 6. 前端设计

### 6.1 新增页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 复盘报告列表 | `/reports` | 历史复盘记录列表 |
| 复盘报告详情 | `/reports/:id` | 单日复盘完整内容 |

### 6.2 新增组件

| 组件 | 说明 |
|------|------|
| LoginModal | 登录/注册弹窗（Tab 切换登录/注册） |
| NotificationBell | 铃铛图标 + 下拉通知列表 |

### 6.3 改造模块

- **Layout.vue**：顶部加铃铛图标，底部用户区改为登录按钮/用户名+退出
- **store/index.js**：增加 user 模块（登录状态、token）；watchlist 模块增加「从后端加载」逻辑
- **Watchlist.vue**：登录后走后端 API，未登录继续 localStorage
- **router/index.js**：加路由守卫（自选股、复盘页需登录）
- **api/**：拆分为 stock.js / auth.js / watchlist.js / report.js / notification.js；axios 实例加请求拦截器注入 token

### 6.4 首次登录数据同步
- 登录成功后检查 localStorage 是否有自选股数据
- 有数据则弹出提示：「检测到本地有 N 只自选股，是否同步到云端？」
- 用户确认后调用 `POST /api/watchlist/sync` 批量导入

### 6.5 消息中心交互
- 铃铛显示未读红点（数字角标，超过 99 显示 99+）
- 点击铃铛展开下拉列表（最近 10 条，按时间倒序）
- 每条显示标题 + 摘要 + 时间，未读高亮
- 点击跳转到对应页面（复盘报告跳详情）并标记已读
- 底部有「查看全部」链接跳转到通知列表页（可做简单版，先不做独立页）

## 7. 错误处理与边界情况

| 场景 | 处理方式 |
|------|---------|
| 用户名已存在 | 返回 400 + 明确提示 |
| 用户名/密码错误 | 返回 401 + 提示 |
| token 过期 | 前端拦截 401 → 清除本地状态 → 弹出登录框 |
| 非交易日定时任务触发 | 跳过（检查当天是否为交易日，或让 APScheduler 只工作日跑，节假日需额外判断，第一版先按工作日处理） |
| 用户没有自选股 | 跳过该用户的复盘生成 |
| AI 调用限流/失败 | 单股失败跳过，整体失败标记 failed，支持手动重试 |
| 同一用户同一天重复生成 | 唯一约束 `(user_id, report_date)` 保证只有一份；手动触发时若已存在则返回已有的（或先删后建，策略待定，第一版：已存在则直接返回） |
| SQLite 并发写入 | 用 SQLAlchemy 的连接池 + 适当的锁，定时任务是单线程写入，风险可控 |

## 8. 配置变更

新增环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | `sqlite:///./stock_analyzer.db` | 数据库连接串 |
| JWT_SECRET_KEY | （必填，随机字符串） | JWT 签名密钥 |
| JWT_ALGORITHM | `HS256` | JWT 算法 |
| JWT_ACCESS_TOKEN_EXPIRE_HOURS | `24` | token 有效期（小时） |
| SCHEDULER_ENABLED | `true` | 是否启用定时任务（开发环境可关） |
| DAILY_REPORT_CRON | `30 15 * * 1-5` | 复盘定时 Cron |

## 9. 非目标（第一版不做）

- 邮箱验证 / 找回密码
- 多设备 token 管理 / refresh token
- 邮件推送 / Webhook 推送
- 自选股导入导出（CSV）
- 报告导出（PDF/图片）
- 节假日判断（仅按周一到周五调度）
- 实时 SSE 推送通知（先轮询或进入页面时拉取）

## 10. 文件结构变更

### 后端新增

```
backend/app/
├── database.py              # SQLAlchemy engine + SessionLocal + Base
├── dependencies.py          # get_current_user, get_db 等依赖
├── models/
│   ├── __init__.py
│   ├── user.py              # User ORM model
│   ├── watchlist.py         # WatchlistGroup, WatchlistItem
│   ├── report.py            # DailyReport, StockReport
│   └── notification.py      # Notification
├── schemas/
│   ├── __init__.py
│   ├── auth.py              # 注册/登录相关 Pydantic
│   ├── watchlist.py
│   ├── report.py
│   └── notification.py
├── routes/
│   ├── auth.py
│   ├── watchlist.py
│   ├── report.py
│   └── notification.py
└── services/
    ├── auth_service.py
    ├── watchlist_service.py
    ├── report_service.py    # 复盘生成逻辑
    ├── notification_service.py
    └── scheduler.py         # APScheduler 初始化 + 任务注册
```

### 后端修改

- `main.py`：初始化数据库、注册新路由、启动 scheduler
- `config.py`：新增配置项
- `requirements.txt`：新增 sqlalchemy、passlib[bcrypt]、python-jose[cryptography]、apscheduler
- `.env.example`：新增环境变量示例

### 前端新增

```
frontend/src/
├── views/
│   ├── Reports.vue          # 复盘列表
│   └── ReportDetail.vue     # 复盘详情
├── components/
│   ├── LoginModal.vue       # 登录注册弹窗
│   └── NotificationBell.vue # 消息铃铛
├── api/
│   ├── auth.js
│   ├── watchlist.js
│   ├── report.js
│   └── notification.js
└── store/
    └── user.js              # 用户状态 store
```

### 前端修改

- `store/index.js`：改造 watchlist store，支持云端模式
- `components/Layout.vue`：加铃铛 + 登录入口
- `router/index.js`：加路由 + 守卫
- `views/Watchlist.vue`：适配云端数据
- `api/stock.js`：拆出通用 axios 实例，加 token 拦截器
- `main.js` / `App.vue`：加全局登录弹窗
