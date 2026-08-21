# 项目进度

最后更新：2026-08-19

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

#### 前端页面
| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 首页/市场概览 | `/` | ✅ | 三大指数 + 市场情绪 + 热门板块 + AI 点评 |
| 个股详情 | `/stock/:code` | ✅ | 行情栏 + K线图 + 财务 + AI 分析 |
| 自选股 | `/watchlist` | ✅ | 分组管理 + 成本 + 盈亏计算 |
| 板块监控 | `/board` | ✅ | 行业/概念 Tab + 板块详情抽屉 |

#### 技术指标（K线副图）
- 成交量（柱状）
- MACD（DIF/DEA/MACD柱）
- KDJ（K/D/J 三线）
- RSI（6/12/24 日）

### 🔧 架构特性
- **多数据源 fallback**：东财 → 同花顺 → 旧缓存，网络波动自动降级
- **内存缓存 + 定时刷新**：板块 2min、市场概览 1min，首次同步加载
- **AKShare 懒加载**：未安装也能启动，使用时才 import
- **重试机制**：`@_retry` 装饰器，指数退避
- **CORS 配置**：支持 localhost:5173

## 文件结构速查

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口 + 启动预加载
│   ├── config.py            # 配置（火山引擎 Claude 兼容）
│   ├── models/schemas.py    # Pydantic 数据模型
│   ├── routes/
│   │   ├── stock.py         # 股票相关 API
│   │   └── board.py         # 板块 + 市场 API
│   └── services/
│       ├── stock_data.py    # 股票数据 + 技术指标计算
│       ├── board_data.py    # 板块数据（多源 fallback）
│       ├── market_data.py   # 市场概览（指数+涨跌统计+涨跌停）
│       ├── ai_analyst.py    # AI 分析（个股 + 市场点评）
│       └── data_cache.py    # 缓存管理 + 定时刷新
├── requirements.txt
└── .env.example

frontend/
├── src/
│   ├── views/               # Dashboard / StockDetail / Watchlist / BoardMonitor
│   ├── components/          # StockSearch / StockInfo / KLineChart / FinancialCard / AiAdvice / Layout
│   ├── api/stock.js         # API 封装
│   ├── store/index.js       # Pinia 自选股 store
│   └── router/index.js      # 路由
└── vite.config.js           # /api 代理到 8000
```

## 已知问题 & 注意事项

1. **东财接口网络问题**：`*_em` 后缀的接口在某些网络环境可能 Connection reset，代码已做多源 fallback
2. **涨跌家数精度**：优先全量行情统计，失败时用行业板块估算（会有偏差）
3. **AI 配置**：需要 `ARK_API_KEY` + `ARK_MODEL`，未配置时显示友好提示
4. **非交易时段**：实时行情可能延迟，K线数据作为降级方案更稳定
5. **自选股存储**：localStorage，无后端用户系统

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

## 后续可做

- [ ] 自选股服务端持久化 + 用户系统
- [ ] K线更多指标（BOLL、OBV、WR 等）
- [ ] 盘后 AI 自动复盘 + 推送
- [ ] 多股对比功能
- [ ] 选股器（按财务/技术指标筛选）
- [ ] 回测功能
