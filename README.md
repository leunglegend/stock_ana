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
├── frontend/          # Vue 前端
│   ├── src/
│   │   ├── components/   # 组件
│   │   │   ├── StockSearch.vue     # 股票搜索
│   │   │   ├── StockInfo.vue       # 行情信息
│   │   │   ├── KLineChart.vue      # K线图
│   │   │   ├── FinancialCard.vue   # 财务指标
│   │   │   └── AiAdvice.vue        # AI 分析建议
│   │   ├── views/
│   │   │   └── Dashboard.vue       # 仪表盘主页
│   │   ├── api/
│   │   │   └── stock.js            # API 封装
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
└── backend/           # Python 后端
    ├── app/
    │   ├── main.py         # FastAPI 入口
    │   ├── config.py       # 配置
    │   ├── routes/
    │   │   └── stock.py    # 股票 API 路由
    │   ├── services/
    │   │   ├── stock_data.py   # AKShare 数据服务
    │   │   └── ai_analyst.py   # AI 分析服务
    │   └── models/
    │       └── schemas.py  # 数据模型
    ├── requirements.txt
    └── .env.example
```

## 快速开始

### 1. 克隆项目

```bash
cd stock-analyzer
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入火山引擎 API Key
```

配置 API（二选一）：

**方式一：环境变量（推荐，更安全）**
```bash
export ANTHROPIC_AUTH_TOKEN=你的_api_key
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
export ARK_MODEL=claude-3-5-sonnet-20241022

# 数据库（默认 SQLite，可省略）
export DATABASE_URL=sqlite:///./stock_analyzer.db

# JWT 密钥（必须配置，用于用户系统）
export JWT_SECRET_KEY=你的随机密钥字符串
```

**方式二：.env 文件**
```bash
cp .env.example .env
# 编辑 .env 填入 API Key 和 JWT 密钥
```

> 火山引擎 Coding Plan 开通：https://www.volcengine.com/product/ark

> JWT 密钥可以用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成

启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后，访问 http://localhost:8000/docs 可以看到 Swagger API 文档。

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后，访问 http://localhost:5173 即可使用。

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
