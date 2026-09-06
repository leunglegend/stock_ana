# 引入"个股新闻 / 公告"能力 — 数据源可行性评估

- 日期：2026-09-03
- 范围：只读调研；不落业务代码。评估"个股新闻（含公司公告）"为平台与 AI 决策报告提供上下文的能力。
- 验证环境：仓库自带 venv，`akshare 1.18.94`；系统日期 2026-09-03；以下"实测"均指从当前开发机（UTC+7）实际调用，**部署环境（尤其中国大陆服务器）需复测连通性**。
- 关联设计：`docs/design-rounds/2026-09-03-us-stock/02-us-page-ia.md`（美股页 IA，一期不做美股个股详情，预留二期 `/us/stock/:symbol`）；现有 A 股 `GET /api/stock/{code}/decision-report` 的 `data_quality.warnings` 写明"当前未接入新闻、公告、资金流和盈利预期数据"（`backend/app/routes/stock.py`）。

---

## 0. 结论速览（TL;DR）

| 维度 | 结论 |
|---|---|
| 可行性分级 | **A 股个股新闻/公告：可行（低成本，接口已实测）**；**美股个股新闻：部分可行**（大型美股中文覆盖可用；全覆盖需依赖英文源/SEC，作为二期） |
| 推荐组合（MVP） | ① A 股：东财个股新闻（`stock_news_em`）+ 东财个股公告（`stock_individual_notice_report`），直接喂给决策报告，消除 data_quality 告警；② 美股页 AI 主线：复用 7×24 快讯池（财联社/东财/同花顺/新浪，已实测实时）做市场级叙事，不做逐个股；③ 二期美股个股：Google News RSS（无 key）+ SEC EDGAR（美股官方公告）。 |
| 时效真实上限 | 快讯池：分钟级实时（已实测当日 23:00 仍有美股快讯）；东财个股新闻：覆盖近 ~2 月、非严格时间序、单次最多 10 条；A 股公告：以日为单位、T+0 披露日可见；Google News RSS：聚合延迟约 0.5~2 小时。 |
| 诚实失败记录 | 巨潮公告接口（cninfo）本机**实测不通**（反爬）；AKShare **无**美股公告/美股逐股新闻封装；`stock_news_em` 查冷门美股 ticker 返回空（RIVN）；公告/研报接口传美股代码直接报错。 |

---

## 1. AKShare 新闻/公告类接口盘点（第 1 问）

列目录命令（只读，已执行）：

```python
import akshare
print([x for x in dir(akshare) if 'news' in x.lower() or 'announcement' in x.lower() or 'notify' in x.lower()])
```

命中的、与本需求（**个股**新闻/公告）相关项及**实测结果**：

| AKShare 函数 | 数据源 | 粒度 | 是否按个股代码 | 实测 | 关键字段 |
|---|---|---|---|---|---|
| `stock_news_em(symbol)` | 东方财富新闻**全库搜索**（非独立个股 feed） | 单次固定 10 条 | 按代码**关键字**搜，A 股代码/美股 ticker/中文名均可 | ✅ 通，约 1-3s | 关键词、新闻标题、新闻内容(摘要)、发布时间、文章来源、新闻链接 |
| `stock_individual_notice_report(security, ...)` | 东财数据中心·公告大全·个股 | 按日期范围 | ✅ A 股 6 位代码 | ✅ 通，需给起止日期（不给会翻全量历史，慢 ~40s） | 代码、名称、公告标题、公告类型、公告日期、网址 |
| `stock_notice_report(type, date)` | 东财公告大全·沪深京（**全市场按日**） | 按日全市场 | ❌ 非单股 | 未单测（`stock_individual_notice_report` 内部复用它） | — |
| `stock_zh_a_disclosure_report_cninfo(...)` | 巨潮资讯·信息披露公告（官方披露源） | 按个股+类型+日期 | ✅ A 股 | ❌ **JSONDecodeError，反爬/本网络不通** | — |
| `stock_research_report_em(symbol)` | 东财数据中心·个股研报 | 单股全量 | ✅ A 股 | ✅ 通（600519 返回 771 条；含近一月研报数与盈利预测） | 报告名称、东财评级、机构、日期、报告PDF链接、盈利预测 |
| `stock_info_global_cls('全部'/'重点')` | 财联社·电报 | 市场级 7×24 快讯 | ❌ | ✅ 通，约 4s，20 条 | 标题、内容、发布日期、发布时间 |
| `stock_info_global_em()` | 东财·全球财经快讯 | 市场级 7×24 | ❌ | ✅ 通，200 条 | 标题、摘要、发布时间、链接 |
| `stock_info_global_ths()` | 同花顺·全球财经直播 | 市场级 7×24 | ❌ | ✅ 通，20 条 | 标题、内容、发布时间、链接 |
| `stock_info_global_sina()` | 新浪·7×24 | 市场级 | ❌ | ✅ 通，20 条 | 时间、内容 |
| `stock_info_global_futu()` | 富途·快讯 | 市场级 | ❌ | ✅ 通，50 条 | 标题、内容、发布时间、链接 |

确认要点：
- **A 股"个股新闻 + 公司公告"在 AKShare 内都有可用封装**，公告按单只股票、可带日期范围；新闻本质是东财搜索，不是独立 feed（见 §2 的坑）。
- **AKShare 没有任何"美股个股公告/美股逐股新闻"封装**。`stock_us_*` 仅有行情/财务/估值类；美股相关的新闻只有上表的**市场级快讯池**。
- 其余命中项（`news_cctv`/`news_economic_baidu`/`news_report_time_baidu`/`news_trade_notify_*`/`fund_announcement_*` 等）为宏观/基金/日历类，与个股新闻无关。
- 快讯池实测**非常实时**：本机测试时为北京时间 23:00 左右（A 股已收盘），财联社/东财/同花顺返回的全是**当日美股盘中/盘前快讯**（特斯拉、纳指、盘前盘后），说明它 7×24 滚动、且覆盖美股时段，天然适合"美股复盘"叙事源。

---

## 2. 关键接口的可用性与坑（第 2 问）

### 2.1 `stock_news_em` — 最顺手的 A 股个股新闻，但有三个坑
实测代码 `600519` 与 `TSLA`/`特斯拉`/`AAPL`/`苹果`，均 1-3s 返回 10 条：

1. **不是"该股最近 N 条"，而是全站关键字搜索**：命中文章只要正文/标题出现该代码或名称即被召回，存在噪声（600519 的结果里有"险资重仓五粮液"这种只顺带提茅台的；TSLA 里有与特斯拉无关的存储芯片快讯）。
2. **排序按相关度而非时间**：返回的 10 条里新旧混杂（600519 首条是 2026-08-15、次条是 2026-09-02；TSLA 首条 2026-08-06）。接入时必须自行按 `发布时间` 降序重排。
3. **固定一页、最多 10 条**：akshare 源码里 `pageIndex=1, pageSize=10` 写死（底层 `search-api-web.eastmoney.com/search/jsonp` 支持翻页，但未暴露）。要更多/更准需自写一个小封装调底层接口加页数、加"标题含代码"过滤。这是"新增接口"里唯一需要脱离 akshare 自研的点。

### 2.2 `stock_individual_notice_report` — A 股公告最靠谱
- 传 6 位 A 股代码 + 起止日期即可，**必须带日期范围**（不带会翻全量历史：600519 无日期实测耗时 41s、拉回 1074 条）。
- 带近 2 月范围：600519 7 条、000001 13 条，2-5s 返回。字段含公告类型（如"半年度报告摘要/调研活动/其他"），可直接喂 AI 归纳最新动态。
- 传美股代码（AAPL）实测 `KeyError`，仅支持 A 股。

### 2.3 `stock_zh_a_disclosure_report_cninfo` — 官方披露源，但**本机实测不通**
- 巨潮是沪深交易所官方披露汇总，理论最优；但本机 GET 直连返回 HTTP 500、akshare 调用抛 `JSONDecodeError`（POST 反爬被拦）。需要额外 header/cookie/重试策略才能用，**不建议作为 MVP 依赖**；东财公告已覆盖同样场景。
- 若需要**公告全文 PDF/正文**，巨潮仍是唯一全量源，属自研爬虫范围（成本另行评估）。

### 2.4 快讯池（财联社/东财/同花顺/新浪/富途）— 市场级实时
- 全部实测可通、当日有数据；列含"标题/内容/发布时间"；东财的还带摘要和原文链接。返回条数 20-200 条/次。
- **不按个股打标**，但可后端按"板块领涨股/指数/关键词"做包含过滤（如标题含"特斯拉/NVDA/英伟达"）后当作个股上下文。
- 非交易时段照常工作（实测 A 股收盘后美股时段仍持续输出）——这是它与个股新闻的最大差异与价值。

### 2.5 AKShare 美股公告
**不存在**。`stock_us_*` 全部是行情/财务/估值。美股"公司公告"等价物是 SEC 申报文件（8-K/10-K/4），AKShare 无封装，见 §3 替代路径。

---

## 3. 替代路径评估（第 3 问）

以下均为本机实测连通/有据可查，免费档即可满足 MVP：

| 候选源 | 实测/成本 | 覆盖 | 时效 | 关键限制 |
|---|---|---|---|---|
| **Google News RSS**（`news.google.com/rss/search?q=<keyword>`） | ✅ 本机实测 200；无需 key、无需注册 | 美股 ticker + A 股代码/中文名都行；本机测 `NVDA stock`(zh) 100 条、`600519 贵州茅台`(zh) 78 条 | 聚合延迟约 0.5-2h | 结果经 google 跳转链接（非原文直链）；聚合源质量参差；**中国大陆服务器直连 Google 通常不可用**；非官方、无 SLA、条款灰色 |
| **Yahoo Finance RSS headline**（`feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL`） | ✅ 本机实测 200，无需 key | 美股 ticker 英文标题 | 近实时 | 非官方公开接口，随时可能失效；英文 |
| **SEC EDGAR**（`data.sec.gov/submissions/CIK{n}.json` + `company_tickers.json` 映射） | ✅ 本机实测 200（需带 `User-Agent` 描述性 header）；**官方免费、无需 key** | 美股全量公司官方申报（8-K/10-K/4 等） | T+0 | 英文原文；需 ticker→CIK 映射（官方提供）；礼貌限速 10 req/s |
| **Finnhub `/company-news`** | ✅ 主机可达（401=需 key）；免费 key 申请成本低（邮箱即可） | 美股逐股新闻 | 近实时 | **免费档仅回溯 12 个月**；60 calls/min；英文 |
| **Alpha Vantage `NEWS_SENTIMENT`** | ✅ demo key 实测 200 返回数据；需注册免费 key | 美股/大类资产新闻+情绪分 | 近实时 | **免费档全站共享 25 req/day**，仅够 demo；超限不报 429 而返回 Note，需自检 |
| **Polygon.io（现名 Massive）`/v2/reference/news`** | ✅ 主机可达（401=需 key） | 美股新闻（带相关 ticker 标签） | 近实时 | **免费档 5 req/min 硬顶**，扫全市场吃力；英文 |
| 预置"当日热点/公告摘要"（无实时源，靠缓存+晨报模板） | 不依赖外部源 | 任意 | 滞后 | 只解决"没内容可写"，不解决"为什么今天涨跌" |

结论：
- **美股个股（一期复盘 + 二期个股页）推荐主源 = Google News RSS（按 ticker 拉中文/英文标题）+ SEC EDGAR（美股"公告"）**，两者都无需 key、已实测。Finnhub 免费档是"更稳的备胎"（12 个月回溯、60 calls/min），若产品正式支持美股个股再申请免费 key 即可（申请成本≈一个邮箱，无需付费）。
- **财联社/东财 7×24 快讯池**是美股页"A股用户读得懂的中文市场级叙事"的最优免费源，且与现有 AKShare 技术栈零新增依赖。
- Alpha Vantage 免费档 25 req/day、Polygon 5 req/min：对本产品（要按需给多只个股拉新闻）都不够，仅作兜底，不建议进入推荐组合。

---

## 4. 覆盖与时效的真实上限

| 场景 | 覆盖上限 | 时效上限 |
|---|---|---|
| A 股个股"新闻"（东财搜索） | 有中文财经媒体报道的个股均能召回；召回质量≈搜索相关度，需时间排序+过滤 | 东财索引更新分钟~小时级；单次 10 条且新老混杂，需自行翻页才到 ~数十条/近 2 月 |
| A 股公司公告 | 沪深京全量公告（东财数据中心，官方公告镜像） | 披露日 T+0 可见，按日粒度 |
| A 股研报（可选） | 东财收录券商研报全量 | 近几月都有，含评级/盈利预测 |
| 美股"中文"个股新闻 | 仅**大型/热门**美股（TSLA/AAPL/NVDA/SMCI 等中文报道多的）；冷门 ticker（实测 RIVN）返回空 | 同东财索引 |
| 美股"全量"个股新闻 | Google News RSS / Finnhub / SEC EDGAR 可覆盖任意 ticker | 0.5-2h 聚合延迟（Google）；近实时（Finnhub）；T+0（SEC） |
| 市场级叙事（A 股+美股） | 7×24 快讯池，中美市场均覆盖 | 分钟级实时 |

真实上限的诚实表述：**A 股"新闻"的召回是"搜索级"而非"数据商级"**——做不到像商业终端那样"该股今天 12 条相关新闻一条不漏"，但足够支撑"为什么涨/跌/出公告了"的 AI 上下文。**美股个股的中文覆盖只对龙头有效**，要全量覆盖必须上英文源。

---

## 5. 接入成本估算（结合现有代码）

现有相关代码（已只读核对）：
- 决策报告：`backend/app/routes/stock.py` `get_decision_report` → `generate_decision_report(info, kline, financial, signals)`；`data_quality.warnings` 硬编码在路由 114-116 行。
- AI 侧：`backend/app/services/ai_analyst.py` 的 `_build_decision_report_prompt` 明确向模型写死"新闻、情绪、公告、资金流和盈利预期均未提供"；`latest_developments`/`sentiment` 无输入时默认 `{status:"unavailable"}`（`_normalize_decision_report`）。
- 模型：`backend/app/models/schemas.py` `StockDecisionReport` 已含 `latest_developments: dict` / `data_quality: dict`，前端 `DecisionReport.vue` 已是新增文件（WIP）。

### A 股 MVP 改动面（推荐先做）
| 位置 | 改动 | 估量 |
|---|---|---|
| `models/schemas.py` | 新增 `StockNewsItem{title, content, publish_time, source, url}`、`StockAnnouncementItem{title, type, date, url}` 两个模型 | ~30 行 |
| `services/news_data.py`（新） | ① 包 `stock_news_em` + 自写翻页/按时间排序/过滤；② 包 `stock_individual_notice_report`（默认近 30 天）；③ 可选包快讯池（供美股页/市场 AI 复用），走现有内存缓存 + `run_in_threadpool` 模式 | 1 个新文件 ~150-250 行 |
| `routes/stock.py` | 加 `GET /{code}/news`、`GET /{code}/announcements`（或合成一个） | 2 个端点 |
| `services/ai_analyst.py` | `generate_decision_report` 增可选入参 `news/announcements`；`_build_decision_report_prompt` 有数据时写入、无数据时维持"未提供"约束；系统提示放开"未接入"前提 | ~30-50 行 |
| `routes/stock.py` decision-report | 先拉新闻/公告传给生成函数；`data_quality.warnings` 改为按是否有数据动态给 | ~10 行 |
| 前端 `api/stock.js` + `StockDetail.vue` | 加拉取函数 + 一个新闻/公告面板；`DecisionReport.vue` 展示 `latest_developments` | ~1-2 组件 |

估算：**A 股 MVP ≈ 1 名熟手 2-4 个工作日**（新增 2 个端点、1 个服务文件、提示词接一根线）。

### 美股复盘 AI 主线（配合 02 设计）
只加"快讯池服务 + 给 `/api/us/ai-summary` 喂当日市场级快讯过滤文本"，**不做逐股新闻**；成本 **0.5-1 天**（数据源免费、akshare 现成、走缓存）。

### 美股个股（二期 `/us/stock/:symbol`）
新增：ticker→中文名映射（02 已隐含需要）、Google News RSS 抓取、可选 SEC EDGAR；中文 UI 若展示英文标题还需翻译/双语。估算 **3-5 天**，属二期。

---

## 6. 推荐数据源组合与最终结论

**可行性分级：A 股可行 / 美股部分可行 /（实时全量新闻库）不可行——但产品不需要后者。**

推荐组合：
1. **A 股个股新闻**：`stock_news_em`（自写翻页+时间排序），兜底不足时叠 Google News RSS(zh)。
2. **A 股公司公告**：`stock_individual_notice_report`（近 30 天）。**不用** cninfo（本机不通，非 MVP）。
3. **美股市场级/复盘叙事**：财联社 + 东财 7×24 快讯池（中文、实时、已实测），过滤出领涨板块/领涨股相关条目喂给 AI 主线。
4. **美股个股（二期）**：Google News RSS + SEC EDGAR（公告）；Finnhub 免费档作稳定备胎。

不推荐：Alpha Vantage（25 req/day）、Polygon（5 req/min）、自研抓财经站正文（维护成本高）。

---

## 7. MVP 建议

> 目标：以最小改动，先把决策报告那行"未接入新闻、公告"的告警做成**真数据**，并让美股页 AI 主线"有话可说"。

1. **后端**：建 `news_data.py`，实现 `get_stock_news(code)`（东财搜索翻页+时间降序+去噪）、`get_stock_announcements(code, days=30)`（东财公告）；`routes/stock.py` 加 `GET /api/stock/{code}/news`（合成近 7 日新闻+近 30 日公告，字段标题/时间/来源/链接/类型）。
2. **喂给 AI**：`generate_decision_report` 增可选入参，prompt 有数据时给 5-8 条最新新闻标题+摘要与最近公告；无数据时维持 `unavailable` 降级。`data_quality.warnings` 相应移除"新闻、公告"项。
3. **前端**：`StockDetail.vue` 的决策报告区下方加一个只读"相关新闻 / 公告"列表（链接可点），复用 `base/` 样式。
4. **美股页（顺带）**：`/api/us/ai-summary` 的输入里拼入当日快讯池中与领涨/领跌板块、领涨股相关的 5-10 条中文快讯标题（快讯池接口与缓存已在第 1 步建好）。
5. **不做**：不做逐美股个股新闻、不做公告全文解析、不申请任何第三方 key。全部走 AKShare + 免费 RSS/官方源。

---

## 8. 诚实失败 / 未验证清单

- ❌ `stock_zh_a_disclosure_report_cninfo`（巨潮）：本机 `JSONDecodeError` / HTTP 500，反爬拦截，**未验证可用**。
- ❌ AKShare 无美股公告、无美股逐股新闻接口（查 `dir(akshare)` 的 `stock_us_*` + news 全集确认）。
- ❌ `stock_individual_notice_report('AAPL', ...)` / `stock_research_report_em('AAPL')`：传美股代码直接 `KeyError`。
- ❌ `stock_news_em('RIVN')`（冷门美股）：返回空导致 `KeyError`——**中文源对冷门美股无覆盖**。
- ⚠️ `stock_news_em` 仅 10 条/次、按相关度排序、含噪声（详见 §2.1）；需要时自研翻页封装。
- ⚠️ Google News RSS / Yahoo RSS / SEC EDGAR 为**本机**实测；中国大陆部署环境需复测（Google/Yahoo 大概率不通，SEC 通常可通）。
- ⚠️ 快讯池（财联社等）非交易时段持续输出美股内容——对"个股新闻"语义可能偏市场级，需按名称/代码过滤。
- 未测：`stock_news_main_cx`（财新，判断需订阅、与个股无关）；`news_cctv` 等宏观源（与本需求无关）。

---

## 附：验证命令与参考链接

```python
# akshare 探测
import akshare
[x for x in dir(akshare) if 'news' in x.lower() or 'announcement' in x.lower()]
ak.stock_news_em('600519')                  # ✅ 10 条
ak.stock_news_em('特斯拉') / ('TSLA')         # ✅ 大市值美股有中文结果
ak.stock_individual_notice_report('600519','全部','20260701','20260903')  # ✅ 7 条
ak.stock_research_report_em('600519')        # ✅ 771 条研报
ak.stock_info_global_cls('全部')              # ✅ 财联社电报
ak.stock_info_global_em()                    # ✅ 东财快讯
```

- akshare 个股新闻：`so.eastmoney.com/news/s?keyword=<code>` / `search-api-web.eastmoney.com`
- 公告：`data.eastmoney.com/notices/stock/<code>.html`
- 快讯：财联社 `cls.cn/telegraph`、东财 `kuaixun.eastmoney.com/7_24.html`、新浪 `finance.sina.com.cn/7x24`、同花顺 `news.10jqka.com.cn/realtimenews.html`
- 免费替代：Google News RSS、SEC EDGAR、Finnhub（免费 60/min/12 个月）、Alpha Vantage（免费 25 req/day）、Polygon（免费 5/min）
