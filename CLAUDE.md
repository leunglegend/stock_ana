# 智能股票分析平台

基于 Vue 3 + FastAPI + AKShare + 大模型的股票分析网站。

## 项目结构

```
stock-analyzer/
├── frontend/          # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/        # 页面：Dashboard, StockDetail, Watchlist, BoardMonitor
│   │   ├── components/   # 组件：StockSearch, StockInfo, KLineChart, FinancialCard, AiAdvice, Layout
│   │   ├── api/stock.js  # API 封装（axios + EventSource）
│   │   ├── store/index.js # Pinia 自选股状态（localStorage 持久化）
│   │   └── router/index.js
│   └── vite.config.js  # /api 代理到 localhost:8000
└── backend/           # Python FastAPI 后端
    ├── app/
    │   ├── main.py         # 入口 + 启动预加载
    │   ├── config.py       # 配置（火山引擎 Claude API 兼容）
    │   ├── routes/
    │   │   ├── stock.py    # 股票 API（搜索/行情/K线/财务/AI分析）
    │   │   └── board.py    # 板块 API（行业/概念/市场概览）
    │   ├── services/
    │   │   ├── stock_data.py   # 股票数据（AKShare，新浪+东财双数据源）
    │   │   ├── board_data.py   # 板块数据（东财+同花顺多 fallback）
    │   │   ├── market_data.py  # 市场概览（指数+涨跌统计+涨跌停）
    │   │   ├── ai_analyst.py   # AI 分析（流式输出）
    │   │   └── data_cache.py   # 内存缓存 + 定时刷新
    │   └── models/schemas.py   # Pydantic 数据模型
    └── requirements.txt
```

## 技术栈

- **前端**：Vue 3 + Vite + Element Plus + ECharts + Pinia + Axios
- **后端**：FastAPI + Uvicorn + AKShare + Pydantic + Anthropic SDK
- **AI**：火山引擎 Coding Plan（Claude API 兼容格式），流式 SSE 输出

## 开发约定

- 后端 Python 文件都有 docstring 模块说明
- 板块数据和市场数据用**多数据源 fallback** 策略：东财 → 同花顺 → 旧缓存
- 缓存首次请求同步加载，之后后台异步刷新（详见 `data_cache.py`）
- 前端用 Vite 代理 `/api` 到后端 8000 端口

## 常用命令

```bash
# 后端
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm run dev   # http://localhost:5173
```

## 注意事项

- 非交易时段或网络环境不佳时，东财接口可能连不上（Connection reset），代码已做多源 fallback
- 市场概览的涨跌家数：优先全量个股统计，失败时用行业板块数据估算
- AI 分析接口走 SSE 流式，前端用 EventSource 接收
