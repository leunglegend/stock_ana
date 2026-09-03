# 智能股票分析平台

一个基于 Vue 3 + Python + 大模型的股票分析网站。输入股票代码后，系统自动获取股票行情、K线走势、财务数据，并通过 AI 大模型生成专业的投资分析建议。

## 功能特性

- 🔍 **股票搜索**：支持股票代码/名称模糊搜索
- 📈 **实时行情**：展示股票最新价格、涨跌幅、成交量等核心数据
- 📊 **K线图表**：日/周/月K线，支持 MA5/MA10/MA20 均线，可缩放拖拽
- 💰 **财务指标**：PE、PB、ROE、净利润、营收等关键财务数据
- 🤖 **AI 智能分析**：基于火山引擎 Coding Plan (Claude)，生成专业的投资分析报告
  - 公司业务概况
  - 财务健康度分析
  - 技术面分析
  - 估值水平评估
  - 投资建议（买入/持有/观望/卖出）
  - 风险提示
- ⚡ **流式输出**：AI 分析结果逐字生成，不用等待全部完成
- ⭐ **自选股管理**：分组管理、成本价设置、盈亏计算，支持云端同步
- 👤 **用户系统**：用户名 + 密码注册登录，JWT 鉴权
- 📋 **盘后 AI 复盘**：交易日收盘后自动生成自选股复盘报告
  - 市场总览点评
  - 关注重点标的
  - 逐只个股深度分析
  - 整体风险提示
- 🔔 **消息中心**：复盘完成通知，站内信实时提醒
- 📑 **历史报告**：可查看所有历史复盘记录
- 🖥️ **盘中监控**：聚合市场环境、自选股快照、技术信号和行动队列，支持定时刷新
- 🇺🇸 **美股复盘**（`/us`）：3 大美股指数、11 个 GICS 板块（标普500成分等权口径）、板块内领涨领跌成分、AI 一句话主线（SSE）

## 技术栈

### 前端
- Vue 3 + Vite
- Element Plus（UI 组件库）
- ECharts + vue-echarts（图表）
- Axios（HTTP 请求）

### 后端
- FastAPI（Web 框架）
- AKShare（股票数据源，免费开源）
- 火山引擎 Coding Plan (Claude)（AI 分析，Anthropic API 格式）
- Uvicorn（ASGI 服务器）

## 项目结构

```
stock-analyzer/
├── start.sh                  # 构建前端并启动同源 Web 服务
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── api/              # 后端 API 封装
│   │   ├── components/       # 页面及基础组件
│   │   ├── composables/      # 可复用组合式逻辑
│   │   ├── router/           # 前端路由
│   │   ├── store/            # Pinia 状态管理
│   │   ├── styles/           # 主题与全局样式
│   │   └── views/            # 业务页面
│   ├── package.json
│   └── vite.config.js        # 开发服务器及 API 代理
├── backend/                  # FastAPI 后端
    ├── app/
    │   ├── main.py            # 应用入口与生命周期
    │   ├── config.py          # 环境变量配置
    │   ├── database.py        # 数据库连接
    │   ├── models/            # SQLAlchemy 数据模型
    │   ├── routes/            # HTTP API 路由
    │   ├── schemas/           # 请求与响应模型
    │   └── services/          # 行情、AI、监控与复盘服务
    ├── tests/                 # 后端测试
    ├── requirements.txt
    └── .env.example
└── docs/                      # 设计与实施文档
```

## 快速开始

### 环境要求

- Linux 或 macOS（`start.sh` 需要 Bash）
- Python 3.10+
- Node.js 20.19+ 或 22.12+，以及 npm

### 1. 安装后端依赖

```bash
python3 -m venv backend/venv
backend/venv/bin/pip install -r backend/requirements.txt
```

### 2. 安装前端依赖

```bash
npm --prefix frontend install
```

### 3. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

按需编辑 `backend/.env`。行情、K 线和财务数据无需配置大模型；AI 分析、用户系统等功能需要对应配置。

| 变量 | 是否必填 | 默认值 | 说明 |
|------|----------|--------|------|
| `ARK_API_KEY` / `ANTHROPIC_AUTH_TOKEN` | AI 功能必填 | 空 | Anthropic 兼容 API 密钥 |
| `ARK_BASE_URL` / `ANTHROPIC_BASE_URL` | 否 | 火山引擎 Coding Plan 地址 | API 基础地址 |
| `ARK_MODEL` | AI 功能必填 | `claude-3-5-sonnet-20241022` | 模型名称 |
| `PORT` | 否 | `52764` | 同源 Web 服务端口 |
| `DATABASE_URL` | 否 | `sqlite:///./stock_analyzer.db` | 数据库连接地址 |
| `JWT_SECRET_KEY` | 用户功能必填 | 空 | JWT 签名密钥 |
| `JWT_ACCESS_TOKEN_EXPIRE_HOURS` | 否 | `24` | 登录令牌有效期（小时） |
| `SCHEDULER_ENABLED` | 否 | `true` | 是否启用盘后复盘定时任务 |
| `DAILY_REPORT_CRON` | 否 | `30 15 * * 1-5` | 复盘任务 Cron 表达式 |

生成 JWT 密钥：

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

不要将 `backend/.env` 提交到版本库。

### 4. 一键启动

```bash
./start.sh
```

启动完成后可访问：

- Web 应用：http://localhost:52764
- API 文档：http://localhost:52764/docs
- 健康检查：http://localhost:52764/health

脚本会先构建 `frontend/dist`，再通过 `nohup` 在后台启动 FastAPI，由 `52764` 端口同时提供页面和 `/api` 接口。页面与接口使用同一个协议、主机和端口，因此不存在浏览器跨域请求。脚本不会自动安装依赖或创建 `.env`。

运行信息：

- PID：`backend/.runtime/stock-analyzer.pid`
- 日志：`backend/.runtime/stock-analyzer.log`
- 查看日志：`tail -f backend/.runtime/stock-analyzer.log`
- 停止服务：`kill "$(cat backend/.runtime/stock-analyzer.pid)"`

重复执行脚本时，如果 PID 对应的进程仍在运行，脚本会拒绝重复启动。

### 手动启动

需要前端热更新时，可在两个终端中进入开发模式。

后端：

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 52764
```

前端：

```bash
cd frontend
npm run dev
```

开发模式访问 http://localhost:5173。Vite 会把 `/api` 请求代理到 `http://localhost:52764`。日常启动建议使用 `./start.sh` 的同源模式。

## 使用说明

1. 在顶部搜索框输入股票代码（如 `600519`）或股票名称（如 `贵州茅台`）
2. 从下拉列表中选择目标股票
3. 页面自动加载行情、K线、财务数据
4. 点击「开始分析」按钮，AI 将生成投资建议
5. 分析结果会逐字显示，等待完整生成后阅读

## API 接口

### 股票 / 板块 / 市场

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 搜索股票 | GET | `/api/stock/search?q=xxx` | 模糊搜索 |
| 股票行情 | GET | `/api/stock/{code}` | 实时行情数据 |
| K线数据 | GET | `/api/stock/{code}/kline` | K线 + 均线 |
| 财务数据 | GET | `/api/stock/{code}/financial` | 财务指标 |
| AI 分析 | GET | `/api/stock/{code}/analyze` | SSE 流式输出 |
| 行业板块 | GET | `/api/board/industry` | 行业板块列表 |
| 概念板块 | GET | `/api/board/concept` | 概念板块列表 |
| 市场概览 | GET | `/api/board/market/summary` | 指数+涨跌统计 |
| 盘中监控总览 | GET | `/api/monitor/overview?group_id=all&days=90` | 需登录；市场环境、自选股快照、技术信号、行动队列；传 `code` 可单只重试 |
| 美股复盘概览 | GET | `/api/us/summary` | 3 大美股指数 + 成分广度 + 领涨/领跌板块 |
| 美股板块涨跌榜 | GET | `/api/us/sectors` | 11 个 GICS 板块等权涨跌，按涨跌幅降序 |
| 板块成分股 | GET | `/api/us/sectors/{name}/constituents` | 板块内领涨领跌成分（标普500 中该 GICS 板块成员） |
| AI 美股复盘 | GET | `/api/us/ai-summary` | SSE 流式一句话主线 |

> 注：美股复盘为收盘口径，板块涨跌**非官方板块指数**，按标普500成分统计（等权聚合）；受数据源限制成分可能部分缺失。本阶段无个股详情与 A 股联动，二期开放。

### 用户系统

| 接口 | 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|------|
| 注册 | POST | `/api/auth/register` | 否 | 用户名+密码注册 |
| 登录 | POST | `/api/auth/login` | 否 | 返回 JWT token |
| 当前用户 | GET | `/api/auth/me` | 是 | 获取用户信息 |

### 自选股（需登录）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 分组列表 | GET | `/api/watchlist/groups` | 含分组下股票 |
| 新建分组 | POST | `/api/watchlist/groups` | |
| 更新分组 | PUT | `/api/watchlist/groups/{id}` | |
| 删除分组 | DELETE | `/api/watchlist/groups/{id}` | |
| 添加股票 | POST | `/api/watchlist/items` | |
| 更新股票 | PUT | `/api/watchlist/items/{id}` | 成本/备注 |
| 删除股票 | DELETE | `/api/watchlist/items/{id}` | |
| 批量同步 | POST | `/api/watchlist/sync` | 支持 replace |

### 复盘报告（需登录）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 报告列表 | GET | `/api/reports` | 分页 |
| 报告详情 | GET | `/api/reports/{id}` | 含个股分析 |
| 手动生成 | POST | `/api/reports/generate` | 后台异步 |

### 消息通知（需登录）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 通知列表 | GET | `/api/notifications` | 分页 |
| 未读数 | GET | `/api/notifications/unread-count` | |
| 标记已读 | PUT | `/api/notifications/{id}/read` | |
| 全部已读 | PUT | `/api/notifications/read-all` | |

## 注意事项

- ⚠️ **免责声明**：AI 生成的分析仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。
- AKShare 依赖第三方数据源，接口可能随时间变动，如遇数据获取失败请升级 AKShare 版本。
- A股交易时间（9:30-11:30, 13:00-15:00）外，实时行情数据可能延迟。
- 火山引擎豆包 API 需要付费使用，请关注调用量和费用。
- 盘中监控采用定时刷新和缓存降级数据，不是逐笔实时行情；第一期不计算持仓数量、仓位和总资产。

## 常见问题

**Q: 不配置火山引擎 API Key 能用吗？**
A: 可以查看行情、K线和财务数据，但 AI 分析和盘后复盘功能不可用。页面会显示提示信息。

**Q: 不配置 JWT 密钥能用吗？**
A: 可以浏览行情、K线、板块等公开数据。但注册登录、自选股云端同步、盘后复盘等用户相关功能需要 JWT 密钥。

**Q: 如何切换其他大模型？**
A: 后端 AI 服务使用 Anthropic 兼容协议，只需修改 `.env` 中的 `ARK_BASE_URL`、`ARK_API_KEY` 和 `ARK_MODEL` 即可切换到其他兼容格式的模型服务。

**Q: 支持哪些股票市场？**
A: 当前版本主要支持 A股（沪深）。如需支持港股/美股，可以扩展后端的 AKShare 数据接口。

**Q: 盘后复盘什么时候触发？**
A: 默认每个交易日（周一到周五）下午 15:30 自动触发，可通过 `DAILY_REPORT_CRON` 环境变量自定义。也可以在报告页面手动触发。

**Q: 自选股数据安全吗？**
A: 自选股数据存储在本地 SQLite 数据库中，每个用户的数据互相隔离。未登录时数据只存在浏览器 localStorage。
