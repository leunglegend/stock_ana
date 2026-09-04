# 美股复盘（页面 + Dashboard 卡片）Implementation Plan

> 执行状态：规划中（未开始）。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增「美股复盘」页面（`/us`）与 Dashboard「美股收盘」摘要卡片：收盘后看 3 大美股指数、11 个 GICS 行业板块等权涨跌与板块内领涨领跌成分股，AI 一句今日主线。

**Architecture:** 后端按已拍板**方案 B** 落地：新浪静态日线为主链路，配一张本地静态「标普500成分 + GICS 行业标签」表做等权聚合；指数层轻、成分层重，因此缓存**按数据自报的美东交易日（`as_of`）判定**、每日仅全量重拉一次，不照抄 A 股 300s TTL。新增独立 `us_universe / us_data / us_cache / routes/us.py`，schema 字段 snake_case 且与 A 股代码空间（6 位数字）隔离（美股 ticker 为字母）。前端独立 `/us` 页面 + 新组件目录 `components/us/`，顶部叙事摘要带（3 指数 + AI 主线 + 领涨/领跌 Top 芯片），下方 11 行全量板块榜、点行右栏下钻成分；Dashboard 在 AI 通栏下追加全宽摘要卡片。

**Tech Stack:** FastAPI、Pydantic v2、AKShare（`index_us_stock_sina` / `stock_us_daily`）、concurrent.futures、Vue 3、Vue Router、Pinia、Element Plus、`api/http.js`(axios)、`composables/useAsyncSection`、Node `node:test`、Python `unittest/pytest`。

**Spec:** 本计划实现已拍板的**方向一「甲骨架 + 乙摘要带」**。规格依据（产品决策轮产物）：
- 数据层调研与方案 B：`docs/design-rounds/2026-09-03-us-stock/01-us-data-layer.md`
- 前端 IA 与方案 A/B：`docs/design-rounds/2026-09-03-us-stock/02-us-page-ia.md`
- 决策结果与评审必改项：`docs/design-rounds/2026-09-03-us-stock/decision-brief.html`（页面形态 = 方案 A 骨架 + 方案 B 顶部叙事摘要带；数据层 = 方案 B）

## Global Constraints

来自决策轮「三方评审共识必改项」（无论选哪套方案都必须遵守）与产品口径，每任务的实现隐含包含本节：

1. **不伪造全市场广度**：涨/跌家数只统计**标普500 成分（约 503 只）**内有效行情。`UsSummary.breadth_scope` 恒为 `"标普500成分口径"`；UI 文案「按标普500成分统计」，不得写「全市场」「涨跌家数 3xxx/4xxx」这类全市场数字。
2. **板块口径必须标注**：板块涨跌幅 = 成分股当日涨跌幅**等权平均**，非官方 GICS 板块指数。`UsSector.method = "equal_weight"`；美股页板块榜副标题固定展示 `标普500成分等权聚合 · 非官方板块指数`，Dashboard 卡领涨/领跌芯片旁同口径小字。
3. **AI 一句话只陈述不归因**：prompt 禁止「由于/受…影响/因为…所以」等归因；每条判断必须能对照 prompt 里给出的可核对数字；数据不足时静态兜底句「今日美股主线暂不明朗」；结尾固定风险句。见 Task 8 的 system prompt。
4. **砍掉空转控件**：美股页无 `el-pagination`、无板块名搜索框、无排序下拉。板块只有 11 个，全量一榜按涨跌幅降序即同时呈现领涨/领跌两端。
5. **涨跌语义沿用平台**：涨 = `--text-positive`（红）、跌 = `--text-negative`（绿），**不要**为美股改成绿涨红跌；市场区分靠文案「美股收盘 · 美东 {as_of}」。
6. **不猜市场开闭状态**：后端不输出 `market_state`。`as_of` 取自数据最近一根 bar 的日期（新浪静态日线在盘中也不更新当日 bar，天然是「最近已入库交易日收盘」口径），页面标题恒为收盘复盘口径并显示 `as_of`。
7. **ticker 与 A 股隔离**：美股 `symbol` 为字母（AAPL），不进入 `/stock/:code` A 股路由；本期成分股行点击**不跳转**，仅保留 `open-symbol` emit 位与 `?sector=` 深链（二期 `/us/stock/:symbol` 再开）。
8. **文本契约风格**：新增 `.vue` 一律用 `SectionPanel / StatusState / PriceDisplay / PercentageDisplay / MetricCell / StockName` 等 base 组件 + `utils/format.js`（`safeNumber` 等），通过现有 `frontend/tests/new-feature-style-contract.test.js`。
9. **导航新增需 4 处**：`router/index.js` 加路由、`components/Layout.vue` `navBlueprint` 加项、`plugins/elementPlus.js` `icons` 白名单注册新图标（本项目导航图标只有注册表里存在才显示）、`DesktopSidebar / MobileNav` 的 `isActive` 加 `/us` 前缀匹配。
10. 美股指数字段为收盘口径且新浪路径无成交额/市值/PE：这些列美股 UI **不展示**，接口对应字段置 0/空（`UsConstituent` 不含市值/PE 字段），不造假。
11. 本期不含：个股新闻、A 股联动映射、美股个股详情页、成分股入自选（均二期；只在数据结构/路由留命名空间注释）。

## 文件与职责映射

### 后端

- Create: `backend/app/data/us_sp500_gics.json` — 静态资产：标普500 成分 `symbol/name_en/sector(GICS EN)` + `as_of/source/count`。
- Create: `backend/scripts/fetch_us_constituents.py` — 数据维护脚本：抓公开数据集（`raw.githubusercontent.com/datasets/s-and-p-500-companies`）CSV → 生成上述 JSON（已探测本环境 HTTP 200）。**不属于 TDD 目标**，产物入库。
- Create: `backend/app/services/us_universe.py` — 加载并校验静态表；GICS EN↔CN 映射、板块元数据。
- Modify: `backend/app/models/schemas.py` — 追加 `UsIndexQuote / UsSector / UsConstituent / UsSummary`。
- Create: `backend/app/services/us_data.py` — 新浪日线抓取（指数 + 成分并发）与纯聚合函数。
- Create: `backend/app/services/us_cache.py` — 按 `as_of` 判定的线程安全快照缓存 + 公开入口。
- Create: `backend/app/routes/us.py` — `/api/us/summary|sectors|sectors/{name}/constituents|ai-summary(SSE)`。
- Modify: `backend/app/services/ai_analyst.py` — 追加美股一句话复盘流式生成（system prompt 内嵌归因禁令）。
- Modify: `backend/app/main.py` — 注册 us router。
- Create: `backend/tests/test_us_universe.py` / `test_us_data.py` / `test_us_cache.py` / `test_us_routes.py`。

### 前端

- Create: `frontend/src/api/us.js` — `getUsSummary / getUsSectors / getUsSectorStocks / getUsAiSummary(SSE)`。
- Create: `frontend/src/composables/useUsMarket.js` — 美股页数据编排（summary + sectors + SSE AI 摘要 + 请求代际）。
- Create: `frontend/src/composables/useUsCard.js` — Dashboard 卡片数据（只调 summary）。
- Create: `frontend/src/components/us/UsIndexStrip.vue` — 3 指数一眼态条。
- Create: `frontend/src/components/us/UsSectorTable.vue` — 11 行全量板块榜。
- Create: `frontend/src/components/us/UsSectorDetailPanel.vue` — 板块下钻（桌面右栏 / 移动 btt 抽屉）。
- Create: `frontend/src/components/dashboard/UsSnapshotCard.vue` — Dashboard 摘要卡。
- Create: `frontend/src/views/UsMarket.vue` — 页面装配 + `?sector=` 深链。
- Modify: `frontend/src/components/dashboard/MarketAiSummary.vue` — `label` prop 化（默认保持现文案，向后兼容）。
- Modify: `frontend/src/router/index.js`、`components/Layout.vue`、`components/app/DesktopSidebar.vue`、`components/app/MobileNav.vue`、`plugins/elementPlus.js`、`views/Dashboard.vue`。
- Create: `frontend/tests/us-api-contract.test.js` / `us-market-contract.test.js` / `us-navigation-contract.test.js`。

### 文档

- Modify: `README.md` — 功能清单加「美股复盘」入口与 `GET /api/us/*` API 表（末尾收尾任务）。

本期不新增数据库表。

---

## Task 1: 标普500 成分静态资产 + universe loader

**Files:**
- Create: `backend/scripts/fetch_us_constituents.py`
- Create: `backend/app/data/us_sp500_gics.json`（脚本产物，入库）
- Create: `backend/app/services/us_universe.py`
- Test: `backend/tests/test_us_universe.py`

**Interfaces:**
- Produces: `us_universe.load_us_constituents() -> list[UsUniverseMember]`；`us_universe.UsUniverseMember`（dataclass：`symbol, name_en, sector_en, sector_cn`）；`us_universe.GICS_EN_TO_CN` / `GICS_CN_TO_EN`（11 项映射 dict）；`us_universe.get_sector_cns() -> list[str]`（固定顺序）。

- [ ] **Step 1: 建 data 与 scripts 目录并写抓取脚本**

```bash
mkdir -p backend/app/data backend/scripts
```

`backend/scripts/fetch_us_constituents.py`（仓库根运行；`urllib`，仅标准库；失败时给出明确非零退出）：

```python
"""抓取标普500成分 + GICS 行业标签，生成 backend/app/data/us_sp500_gics.json（数据维护脚本，季频重跑）。

用法:  python scripts/fetch_us_constituents.py
来源:  https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv
CSV 列: Symbol, Security, GICS Sector, GICS Sub-Industry, ...（GICS Sector 为英文一级行业）
本脚本只取 Symbol/Security/GICS Sector；产物 count 应约 503。
"""
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

CSV_URL = ("https://raw.githubusercontent.com/datasets/s-and-p-500-companies/"
           "master/data/constituents.csv")
OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "us_sp500_gics.json"
EXPECTED_SECTORS = {  # GICS 11 一级行业英文名（与 us_universe.GICS_EN_TO_CN 键一致）
    "Information Technology", "Health Care", "Financials",
    "Consumer Discretionary", "Consumer Staples", "Industrials", "Energy",
    "Materials", "Communication Services", "Utilities", "Real Estate",
}


def main() -> int:
    with urllib.request.urlopen(CSV_URL, timeout=20) as resp:
        text = resp.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    seen, constituents = set(), []
    for r in rows:
        sym = (r.get("Symbol") or "").strip().upper()
        name = (r.get("Security") or "").strip()
        sector = (r.get("GICS Sector") or "").strip()
        if not sym or not sector:
            continue
        if sector not in EXPECTED_SECTORS:
            print(f"警告: 未知 GICS 行业 {sector!r} @ {sym}，跳过", file=sys.stderr)
            continue
        if sym in seen:
            continue
        seen.add(sym)
        constituents.append({"symbol": sym, "name_en": name, "sector": sector})
    constituents.sort(key=lambda x: x["symbol"])
    if not 490 <= len(constituents) <= 520:
        print(f"错误: 成分数量异常 {len(constituents)}，预期约 503", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps({
        "as_of": "2026-09-03",
        "source": "https://github.com/datasets/s-and-p-500-companies (S&P 500 constituents + GICS Sector)",
        "count": len(constituents),
        "constituents": constituents,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {OUT}，共 {len(constituents)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 运行脚本生成资产并目检**

Run: `cd backend && source venv/bin/activate && python scripts/fetch_us_constituents.py`
Expected: 打印 `已写入 .../us_sp500_gics.json，共 5xx 条`；随后 `python -c "import json;d=json.load(open('app/data/us_sp500_gics.json'));print(d['count'], sorted({c['sector'] for c in d['constituents']}))"` 打印 11 个 GICS 英文行业。
（若网络临时失败：重试一次；仍失败则用 `curl -s <CSV_URL>` 落临时文件排查。此步骤产物是数据资产，须提交入库。）

- [ ] **Step 3: 写 loader 失败测试**

`backend/tests/test_us_universe.py`：

```python
import unittest
from app.services import us_universe
from app.services.us_universe import GICS_CN_TO_EN, GICS_EN_TO_CN


class UsUniverseTest(unittest.TestCase):
    def test_gics_mapping_has_11_symmetric_pairs(self):
        self.assertEqual(len(GICS_EN_TO_CN), 11)
        self.assertEqual(set(GICS_EN_TO_CN.values()), set(GICS_CN_TO_EN.keys()))
        self.assertEqual(len(GICS_CN_TO_EN), len(set(GICS_CN_TO_EN)))

    def test_load_real_asset_size_and_shape(self):
        members = us_universe.load_us_constituents()
        self.assertTrue(490 <= len(members) <= 520, f"成分数量异常: {len(members)}")
        symbols = [m.symbol for m in members]
        self.assertEqual(len(symbols), len(set(symbols)), "symbol 必须唯一")
        self.assertTrue(all(m.symbol.isascii() and m.symbol.isupper()
                            for m in members), "symbol 应为大写字母 ticker")
        for m in members:
            self.assertIn(m.sector_cn, us_universe.get_sector_cns())

    def test_known_members_present(self):
        members = us_universe.load_us_constituents()
        by = {m.symbol: m for m in members}
        for sym, expect_cn in [("AAPL", "信息技术"), ("XOM", "能源"),
                               ("JPM", "金融"), ("JNJ", "医疗保健")]:
            self.assertIn(sym, by)
            self.assertEqual(by[sym].sector_cn, expect_cn)
```

- [ ] **Step 4: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_universe.py -v`
Expected: FAIL（`ModuleNotFoundError: app.services.us_universe` 或常量缺失）。

- [ ] **Step 5: 实现 loader**

`backend/app/services/us_universe.py`：

```python
"""美股静态股池（universe）加载与 GICS 板块元数据。

方案 B 的核心数据资产：标普500 成分 + GICS 一级行业标签，季频由
backend/scripts/fetch_us_constituents.py 重新生成。本模块只做加载/校验，
不发起任何网络请求。
"""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "us_sp500_gics.json"

# GICS 11 一级行业 英文 -> 中文（与抓取脚本 EXPECTED_SECTORS 键一致）
GICS_EN_TO_CN = {
    "Information Technology": "信息技术",
    "Health Care": "医疗保健",
    "Financials": "金融",
    "Consumer Discretionary": "非必需消费",
    "Consumer Staples": "必需消费",
    "Industrials": "工业",
    "Energy": "能源",
    "Materials": "原材料",
    "Communication Services": "通信服务",
    "Utilities": "公用事业",
    "Real Estate": "房地产",
}
GICS_CN_TO_EN = {cn: en for en, cn in GICS_EN_TO_CN.items()}

# 固定展示顺序（与官方字母序无关，稳定 UI 排序）
_SECTOR_CN_ORDER = [
    "信息技术", "医疗保健", "金融", "非必需消费", "必需消费", "工业",
    "能源", "原材料", "通信服务", "公用事业", "房地产",
]


@dataclass(frozen=True)
class UsUniverseMember:
    symbol: str
    name_en: str
    sector_en: str

    @property
    def sector_cn(self) -> str:
        return GICS_EN_TO_CN[self.sector_en]


def get_sector_cns() -> list:
    """板块中文名列表，固定顺序，用于遍历与 UI 兜底。"""
    return list(_SECTOR_CN_ORDER)


@lru_cache(maxsize=1)
def load_us_constituents() -> list:
    """读取并校验静态成分表，返回 UsUniverseMember 列表（按 symbol 排序）。

    校验失败（数量/ticker/行业标签异常）直接抛错：宁可启动即失败，
    也不能带着残缺股池聚合出假板块数据。
    """
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    members = []
    seen = set()
    for c in raw["constituents"]:
        sym = c["symbol"]
        if sym in seen:
            raise ValueError(f"成分表重复 ticker: {sym}")
        seen.add(sym)
        if c["sector"] not in GICS_EN_TO_CN:
            raise ValueError(f"成分表含未知 GICS 行业: {c['symbol']} {c['sector']}")
        members.append(UsUniverseMember(symbol=sym, name_en=c["name_en"], sector_en=c["sector"]))
    if not 490 <= len(members) <= 520:
        raise ValueError(f"成分数量异常: {len(members)}")
    return members
```

- [ ] **Step 6: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_universe.py -v`
Expected: 4 个测试 PASS。

- [ ] **Step 7: 提交**

```bash
git add backend/scripts/fetch_us_constituents.py backend/app/data/us_sp500_gics.json backend/app/services/us_universe.py backend/tests/test_us_universe.py
git commit -m "feat(us): 标普500成分+GICS 静态股池与 loader"
```

---

## Task 2: 美股 Pydantic 模型

**Files:**
- Modify: `backend/app/models/schemas.py`
- Test: `backend/tests/test_us_schemas.py`（新增）

**Interfaces:**
- Produces（供 Task 3-8 与前端使用，字段 snake_case）：
  - `UsIndexQuote`：`symbol: str`, `name: str`, `value: float`, `change_amount: float = 0`, `change_pct: float = 0`
  - `UsSector`：`name: str`（中文）, `name_en: str = ""`, `change_pct: float = 0`, `leading_symbol: str = ""`, `leading_name: str = ""`, `leading_change_pct: float = 0`, `advancers: int = 0`, `decliners: int = 0`, `constituent_count: int = 0`, `method: str = "equal_weight"`
  - `UsConstituent`：`symbol: str`, `name: str`（英文名，前端可显示）, `price: float`, `change_amount: float = 0`, `change_pct: float = 0`
  - `UsSummary`：`as_of: str`, `updated_at: str`, `breadth_scope: str = "标普500成分口径"`, `indices: List[UsIndexQuote]`, `advancers: int`, `decliners: int`, `unchanged: int`, `top_gainers: List[UsSector]`, `top_losers: List[UsSector]`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_us_schemas.py`：

```python
import unittest
from app.models.schemas import UsConstituent, UsIndexQuote, UsSector, UsSummary


class UsSchemasTest(unittest.TestCase):
    def test_quote_defaults_and_fields(self):
        q = UsIndexQuote(symbol="DJI", name="道琼斯", value=34850.2, change_pct=1.05)
        self.assertEqual(q.change_amount, 0.0)

    def test_sector_defaults(self):
        s = UsSector(name="信息技术", change_pct=2.1)
        self.assertEqual(s.method, "equal_weight")
        self.assertEqual(s.advancers, 0)

    def test_summary_serializes_nested_lists(self):
        idx = UsIndexQuote(symbol="SPX", name="标普500", value=4512.3, change_pct=0.72)
        sector = UsSector(name="能源", change_pct=-1.8)
        s = UsSummary(as_of="2026-09-02", updated_at="2026-09-03 04:00:00",
                      indices=[idx], top_losers=[sector])
        self.assertEqual(s.breadth_scope, "标普500成分口径")
        data = s.model_dump()
        self.assertEqual(data["top_losers"][0]["method"], "equal_weight")

    def test_constituent_uses_symbol_not_code(self):
        c = UsConstituent(symbol="AAPL", name="Apple Inc.", price=228.2, change_pct=1.1)
        self.assertEqual(c.model_dump()["symbol"], "AAPL")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_schemas.py -v`
Expected: FAIL（`ImportError: cannot import name 'UsIndexQuote'`）。

- [ ] **Step 3: 实现模型**

在 `backend/app/models/schemas.py` 末尾追加：

```python
# ===== 美股复盘（US market，收盘口径）=====

class UsIndexQuote(BaseModel):
    """美股指数收盘快照（新浪静态日线末两根 bar 自算涨跌）。"""
    symbol: str                # SPX / DJI / IXIC / NDX / SOX
    name: str                  # 中文名
    value: float               # 收盘点位
    change_amount: float = 0   # 涨跌点
    change_pct: float = 0      # 涨跌幅(%)


class UsSector(BaseModel):
    """美股 GICS 一级行业板块（标普500成分等权聚合，非官方板块指数）。"""
    name: str                                  # 中文板块名
    name_en: str = ""                          # 英文板块名（GICS）
    change_pct: float = 0                      # 成分当日涨跌幅等权平均(%)
    leading_symbol: str = ""                   # 领涨成分 ticker
    leading_name: str = ""                     # 领涨成分名（英文）
    leading_change_pct: float = 0              # 领涨成分涨跌幅(%)
    advancers: int = 0                         # 板块内上涨成分数
    decliners: int = 0                         # 板块内下跌成分数
    constituent_count: int = 0                 # 板块有效行情成分数
    method: str = "equal_weight"               # 口径: equal_weight


class UsConstituent(BaseModel):
    """标普500 成分（板块成员）收盘行情。"""
    symbol: str                # 字母 ticker
    name: str                  # 英文名（本期无稳定中文个股名来源）
    price: float               # 收盘价
    change_amount: float = 0   # 涨跌额
    change_pct: float = 0      # 涨跌幅(%)


class UsSummary(BaseModel):
    """美股收盘复盘概览（Dashboard 卡与页面摘要区共用一个源）。"""
    as_of: str = ""                              # 美东最近交易日（数据自报）
    updated_at: str = ""                         # 北京时间取数时间
    breadth_scope: str = "标普500成分口径"        # 广度统计范围说明
    indices: List[UsIndexQuote] = []
    advancers: int = 0                           # 成分内上涨数
    decliners: int = 0                           # 成分内下跌数
    unchanged: int = 0                           # 成分内平盘数
    top_gainers: List[UsSector] = []             # 领涨板块 Top3（降序前 3）
    top_losers: List[UsSector] = []              # 领跌板块 Top3（升序前 3）
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_schemas.py -v`
Expected: 4 个测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/app/models/schemas.py backend/tests/test_us_schemas.py
git commit -m "feat(us): 美股复盘 Pydantic 模型（UsIndexQuote/UsSector/UsConstituent/UsSummary）"
```

---

## Task 3: 指数行情抓取（新浪日线 → 涨跌幅自算）

**Files:**
- Create: `backend/app/services/us_data.py`
- Test: `backend/tests/test_us_data.py`

**Interfaces:**
- Consumes: `us_universe.load_us_constituents`、`stock_data._get_ak()`、`stock_data._retry`、`UsIndexQuote`。
- Produces:
  - `us_data.US_INDEX_SYMBOLS`：`tuple[tuple[str,str,str], ...]`，形如 `(".INX", "SPX", "标普500")`（新浪代码, 展示 symbol, 中文名），含 `.INX/.IXIC/.DJI/.NDX/.SOX`，前 3 个为 3 大指数（顺序 DJI/SPX/IXIC 由路由决定）。
  - `us_data.fetch_index_quotes(ak=None) -> list[UsIndexQuote]`（5 条；单指数失败跳过并打印，不拖垮整体）。
  - `us_data.fetch_index_asof(ak=None) -> str | None`：`.INX` 最近 bar date，轻量探测用（1 个请求）。

- [ ] **Step 1: 写失败测试**

`backend/tests/test_us_data.py`（FakeAkshare 注入，仿 `test_board_data_fallback.py` 手法）：

```python
import unittest
import pandas as pd

from app.services import us_data
from app.services.us_data import fetch_index_asof, fetch_index_quotes


def _idx_df(dates, closes):
    return pd.DataFrame({
        "date": dates, "open": closes, "high": closes,
        "low": closes, "close": closes, "volume": [1] * len(closes),
        "amount": [0] * len(closes),
    })


class FakeAkshare:
    def index_us_stock_sina(self, symbol):
        # 元组顺序 = (09-01 收盘, 09-02 收盘)，与日期升序一一对应
        closes = {
            ".INX": (7631.47, 7666.6),      # +0.46%
            ".IXIC": (26099.77, 26217.83),  # +0.45%
            ".DJI": (52766.88, 53061.95),   # +0.56%
            ".NDX": (29077.22, 29143.33),
            ".SOX": (5800.0, 5600.0),        # -3.45%
        }[symbol]
        return _idx_df(["2026-09-01", "2026-09-02"], list(closes))


class IndexFetchTest(unittest.TestCase):
    def test_fetch_index_quotes_returns_expected_pct(self):
        quotes = fetch_index_quotes(ak=FakeAkshare())
        by = {q.symbol: q for q in quotes}
        self.assertAlmostEqual(by["SPX"].change_pct, 0.46, places=2)
        self.assertAlmostEqual(by["DJI"].value, 53061.95)
        self.assertAlmostEqual(by["SOX"].change_pct, -3.45, places=2)
        # 涨跌点 = 末根 - 次末根
        self.assertAlmostEqual(by["SPX"].change_amount, 7666.6 - 7631.47)

    def test_fetch_index_quotes_covers_three_major(self):
        quotes = fetch_index_quotes(ak=FakeAkshare())
        self.assertEqual([q.symbol for q in quotes], ["SPX", "IXIC", "DJI", "NDX", "SOX"])

    def test_fetch_index_asof_is_latest_bar_date(self):
        self.assertEqual(fetch_index_asof(ak=FakeAkshare()), "2026-09-02")

    def test_single_index_failure_is_skipped(self):
        class Flaky(FakeAkshare):
            def index_us_stock_sina(self, symbol):
                if symbol == ".IXIC":
                    raise RuntimeError("connection reset")
                return super().index_us_stock_sina(symbol)

        quotes = fetch_index_quotes(ak=Flaky())
        self.assertNotIn("IXIC", {q.symbol for q in quotes})
        self.assertEqual(len(quotes), 4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_data.py -v`
Expected: FAIL（`ModuleNotFoundError`）。

- [ ] **Step 3: 实现指数抓取**

`backend/app/services/us_data.py`（本步只放指数部分；Task 4 追加成分抓取）：

```python
"""美股收盘行情服务（方案 B 主链路 = 新浪静态日线）。

新浪静态日线在美股盘中也不更新当日 bar（实测 ET 午间请求仍返回上一
交易日完整日量），天然是"最近已入库交易日收盘"口径 —— 与美股页"收盘
复盘"定位一致。板块聚合依赖静态成分表（us_universe）。
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.models.schemas import UsConstituent, UsIndexQuote, UsSector
from app.services import stock_data

# (新浪代码, 展示 symbol, 中文名)；前 3 为 3 大指数，路由取 .DJI/.INX/.IXIC
US_INDEX_SYMBOLS = (
    (".INX", "SPX", "标普500"),
    (".IXIC", "IXIC", "纳斯达克"),
    (".DJI", "DJI", "道琼斯"),
    (".NDX", "NDX", "纳斯达克100"),
    (".SOX", "SOX", "费城半导体"),
)
_MAJOR_INDEX_SYMBOLS = ("DJI", "SPX", "IXIC")  # 摘要/卡片展示用 3 大指数


def _close_pct(price: float, prev_close: float) -> tuple:
    change = price - prev_close
    pct = (price / prev_close - 1) * 100 if prev_close else 0.0
    return change, pct


@stock_data._retry(max_retries=2, delay=1)
def _index_frame(ak, symbol: str):
    return ak.index_us_stock_sina(symbol=symbol)


def _frame_latest(frame):
    """frame 按 date 升序排序后返回 (date, close, prev_close)；不足两根返回 None。"""
    df = frame.sort_values("date").reset_index(drop=True)
    if len(df) < 2:
        return None
    last, prev = df.iloc[-1], df.iloc[-2]
    return str(last["date"]), float(last["close"]), float(prev["close"])


def fetch_index_quotes(ak=None) -> list:
    """拉 5 个美股指数的收盘涨跌（单指数失败跳过，不拖垮整体）。"""
    ak = ak or stock_data._get_ak()
    quotes = []
    for code, symbol, cn in US_INDEX_SYMBOLS:
        try:
            latest = _frame_latest(_index_frame(ak, code))
            if not latest:
                continue
            date, close, prev = latest
            change, pct = _close_pct(close, prev)
            quotes.append(UsIndexQuote(symbol=symbol, name=cn, value=close,
                                       change_amount=change, change_pct=pct))
        except Exception as e:
            print(f"[us] 指数 {code} 拉取失败: {e}")
    return quotes


def fetch_index_asof(ak=None) -> Optional[str]:
    """轻量探测最新美东交易日（标普500 日线最近 bar date，1 个请求）。"""
    ak = ak or stock_data._get_ak()
    try:
        latest = _frame_latest(_index_frame(ak, ".INX"))
        return latest[0] if latest else None
    except Exception as e:
        print(f"[us] as_of 探测失败: {e}")
        return None
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_data.py -v`
Expected: 4 个测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/us_data.py backend/tests/test_us_data.py
git commit -m "feat(us): 新浪美股指数日线抓取与收盘涨跌自算"
```

---

## Task 4: 成分股日线抓取（并发）与解析

**Files:**
- Modify: `backend/app/services/us_data.py`（追加）
- Test: `backend/tests/test_us_data.py`（追加类）

**Interfaces:**
- Consumes: `us_universe.load_us_constituents()`、`UsUniverseMember`、`UsConstituent`。
- Produces:
  - `us_data.parse_us_daily(frame) -> dict | None`：纯函数，返回 `{"date","price","change_amount","change_pct"}`，取末两根 bar 收盘自算；<2 根返回 None。
  - `us_data.fetch_constituent_quotes(members, ak=None, max_workers=16) -> tuple[list[UsConstituent], str | None]`：并发逐成分拉 `stock_us_daily(symbol=…)`；返回 `(quotes, as_of)`，`as_of` = 成功成分 bar date 的众数（最晚交易日）；整体失败返回 `([], None)`。
  - `us_data.fetch_one_quote(members, symbol, ak) -> UsConstituent | None`（供单点重试/路由下钻按需单拉可选，本期主要用于组合 fetch 内部）。

- [ ] **Step 1: 写失败测试**

在 `backend/tests/test_us_data.py` 追加：

```python
from app.services.us_data import (
    fetch_constituent_quotes, parse_us_daily,
)


def _stock_frame(closes):
    dates = [f"2026-09-0{i + 1}" for i in range(len(closes))]
    return pd.DataFrame({
        "date": dates, "open": closes, "high": closes, "low": closes,
        "close": closes, "volume": [1] * len(closes),
    })


class DailyParserTest(unittest.TestCase):
    def test_parse_us_daily_computes_close_change(self):
        frame = _stock_frame([100.0, 105.0])
        r = parse_us_daily(frame)
        self.assertEqual(r["date"], "2026-09-02")
        self.assertEqual(r["price"], 105.0)
        self.assertEqual(r["change_amount"], 5.0)
        self.assertAlmostEqual(r["change_pct"], 5.0)

    def test_parse_us_daily_requires_two_bars(self):
        self.assertIsNone(parse_us_daily(_stock_frame([100.0])))

    def test_frame_with_unsorted_dates_is_sorted_first(self):
        # 行乱序：首行是较晚日期，须先按 date 升序再取末两根 bar
        frame = pd.DataFrame({
            "date": ["2026-09-02", "2026-09-01"],
            "open": [200.0, 100.0], "high": [200.0, 100.0],
            "low": [200.0, 100.0], "close": [200.0, 100.0],
            "volume": [1, 1],
        })
        r = parse_us_daily(frame)
        self.assertEqual(r["price"], 200.0)      # 09-02 收盘
        self.assertEqual(r["change_pct"], 100.0)  # 100 -> 200


class FakeDailyAkshare:
    """index_us_stock_sina 同 Task 3；stock_us_daily 返回每股两根 bar。"""
    closes = {"AAPL": [228.0, 230.0], "MSFT": [415.0, 410.0], "XOM": [112.0, 110.0]}

    def index_us_stock_sina(self, symbol):  # 兼容 fetch_index_asof
        return _idx_df(["2026-09-01", "2026-09-02"], [7666.6, 7631.47])

    def stock_us_daily(self, symbol, adjust=""):
        if symbol not in self.closes:
            raise RuntimeError(f"unknown {symbol}")
        return _stock_frame(self.closes[symbol])


class ConstituentFetchTest(unittest.TestCase):
    def test_fetch_quotes_aggregates_and_derives_asof(self):
        from app.services.us_universe import UsUniverseMember
        members = [UsUniverseMember("AAPL", "Apple", "Information Technology"),
                   UsUniverseMember("MSFT", "Microsoft", "Information Technology"),
                   UsUniverseMember("XOM", "Exxon", "Energy")]
        quotes, as_of = fetch_constituent_quotes(members, ak=FakeDailyAkshare())
        by = {q.symbol: q for q in quotes}
        self.assertEqual(as_of, "2026-09-02")
        self.assertAlmostEqual(by["AAPL"].price, 230.0)
        self.assertAlmostEqual(by["AAPL"].change_pct, 200.0 / 228.0 * 100 - 100)  # ~0.877
        self.assertAlmostEqual(by["MSFT"].change_pct, -1.2048, places=2)
        self.assertEqual(by["XOM"].name, "Exxon")

    def test_partial_failure_keeps_successes(self):
        from app.services.us_universe import UsUniverseMember
        members = [UsUniverseMember("AAPL", "Apple", "Information Technology"),
                   UsUniverseMember("BAD", "Broken", "Energy")]

        class Flaky(FakeDailyAkshare):
            def stock_us_daily(self, symbol, adjust=""):
                if symbol == "BAD":
                    raise RuntimeError("connection reset")
                return super().stock_us_daily(symbol, adjust)

        quotes, as_of = fetch_constituent_quotes(members, ak=Flaky())
        self.assertEqual([q.symbol for q in quotes], ["AAPL"])
        self.assertEqual(as_of, "2026-09-02")


if __name__ == "__main__":
    unittest.main()
```

（注意：测试文件现有 `_idx_df` 在第 1 行 import pd 之后已定义；`us_data` 内 `fetch_index_asof` 用不到此处不需要。）

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_data.py -v`
Expected: 新增 5 个测试 FAIL（`ImportError`）。

- [ ] **Step 3: 实现成分抓取**

在 `us_data.py` 追加（`fetch_constituent_quotes` 用线程池并发；`_fetch_single` 同时返回行情与 bar 日期，供 as_of 推导）：

```python
def parse_us_daily(frame) -> Optional[dict]:
    """静态日线末两根 bar 收盘自算；返回 date/price/change_amount/change_pct。"""
    latest = _frame_latest(frame)
    if not latest:
        return None
    date, close, prev = latest
    change, pct = _close_pct(close, prev)
    return {"date": date, "price": close,
            "change_amount": change, "change_pct": pct}


@stock_data._retry(max_retries=2, delay=1)
def _stock_daily_frame(ak, symbol: str):
    return ak.stock_us_daily(symbol=symbol)


def _fetch_single(member, ak):
    """单成分拉取。失败打日志但不抛出（个股失败不影响整体）。"""
    try:
        parsed = parse_us_daily(_stock_daily_frame(ak, member.symbol))
    except Exception as e:
        print(f"[us] 成分 {member.symbol} 拉取失败: {e}")
        return None, None
    if not parsed:
        return None, None
    q = UsConstituent(symbol=member.symbol, name=member.name_en,
                      price=parsed["price"], change_amount=parsed["change_amount"],
                      change_pct=parsed["change_pct"])
    return q, parsed["date"]


def fetch_constituent_quotes(members, ak=None, max_workers=16) -> tuple:
    """并发拉成分日线；返回 (成功 quotes 列表, as_of)。

    as_of = 成功成分 bar date 的众数（多数成分共有的最晚 bar date，即最近已入库
    美东交易日；避免个别停牌/退市股把日期带偏）。整体失败返回 ([], None)。
    """
    ak = ak or stock_data._get_ak()
    quotes, dates = [], []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_fetch_single, m, ak): m.symbol for m in members}
        for fut in as_completed(futs):
            try:
                q, date = fut.result()
            except Exception as e:  # 防御：线程层未预期异常不拖垮整体
                print(f"[us] 成分线程异常: {e}")
                continue
            if q is not None:
                quotes.append(q)
                dates.append(date)
    if not quotes:
        return [], None
    as_of = max(set(dates), key=dates.count) if dates else None
    return quotes, as_of
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_data.py -v`
Expected: 全部 PASS（原 4 + 新 5）。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/us_data.py backend/tests/test_us_data.py
git commit -m "feat(us): 新浪成分日线并发抓取（线程池 + 失败跳过 + as_of 众数）"
```

---

## Task 5: 板块聚合 + 概览合成（纯函数）

**Files:**
- Modify: `backend/app/services/us_data.py`（追加聚合）
- Test: `backend/tests/test_us_data.py`（追加类）

**Interfaces:**
- Consumes: `us_universe.load_us_constituents`、Task 2 的 `UsSector/UsSummary`。
- Produces:
  - `us_data.aggregate_sectors(members, quotes) -> list[UsSector]`：按 GICS 中文板块分组等权平均；`advancers/decliners/constituent_count/leading_*` 实算；按 `change_pct` 降序返回。
  - `us_data.sector_constituents(members, quotes, sector_cn) -> list[UsConstituent]`：按板块筛出成分并按 `change_pct` 降序。
  - `us_data.compose_summary(indices, sectors, as_of) -> UsSummary`：3 大指数（按 `_MAJOR_INDEX_SYMBOLS` 顺序）+ 成分口径广度 + `top_gainers=前3 / top_losers=后3` + `updated_at`（北京 `datetime.now().strftime`）。

- [ ] **Step 1: 写失败测试**

在 `backend/tests/test_us_data.py` 追加：

```python
from app.services import us_data
from app.services.us_data import (
    aggregate_sectors, compose_summary, sector_constituents,
)
from app.services.us_universe import UsUniverseMember
from app.models.schemas import UsConstituent, UsIndexQuote, UsSector


def _mk_members():
    return [
        UsUniverseMember("AAPL", "Apple", "Information Technology"),
        UsUniverseMember("MSFT", "Microsoft", "Information Technology"),
        UsUniverseMember("NVDA", "NVIDIA", "Information Technology"),
        UsUniverseMember("XOM", "Exxon", "Energy"),
        UsUniverseMember("CVX", "Chevron", "Energy"),
    ]


def _mk_quotes():
    vals = {"AAPL": 2.0, "MSFT": -1.0, "NVDA": 5.0, "XOM": -3.0, "CVX": 1.0}
    out = []
    for sym, pct in vals.items():
        price = 100.0 + pct
        out.append(UsConstituent(symbol=sym, name=sym, price=price,
                                 change_amount=pct, change_pct=pct))
    return out


class SectorAggregateTest(unittest.TestCase):
    def test_equal_weight_and_advancers_decliners(self):
        sectors = aggregate_sectors(_mk_members(), _mk_quotes())
        by = {s.name: s for s in sectors}
        it = by["信息技术"]
        # (2 -1 +5)/3 = 2.0
        self.assertAlmostEqual(it.change_pct, 2.0, places=6)
        self.assertEqual(it.advancers, 2)   # AAPL/NVDA 涨
        self.assertEqual(it.decliners, 1)   # MSFT 跌
        self.assertEqual(it.constituent_count, 3)
        self.assertEqual(it.leading_symbol, "NVDA")
        self.assertEqual(it.leading_change_pct, 5.0)
        self.assertEqual(it.method, "equal_weight")

    def test_sectors_sorted_desc(self):
        sectors = aggregate_sectors(_mk_members(), _mk_quotes())
        self.assertEqual([s.change_pct for s in sectors],
                         sorted([s.change_pct for s in sectors], reverse=True))

    def test_missing_quote_member_is_excluded(self):
        members = _mk_members() + [UsUniverseMember("ZZZZ", "Ghost", "信息技术" if False else "Energy")]
        # ZZZZ 无行情，须不影响 Energy 板块
        sectors = aggregate_sectors(members, _mk_quotes())
        en = next(s for s in sectors if s.name == "能源")
        self.assertEqual(en.constituent_count, 2)

    def test_sector_constituents_filters_and_sorts(self):
        stocks = sector_constituents(_mk_members(), _mk_quotes(), "信息技术")
        self.assertEqual([s.symbol for s in stocks], ["NVDA", "AAPL", "MSFT"])

    def test_empty_quotes_yields_empty_sectors(self):
        self.assertEqual(aggregate_sectors(_mk_members(), []), [])


class SummaryComposeTest(unittest.TestCase):
    def test_compose_summary_major_indices_and_breadth(self):
        indices = [UsIndexQuote(symbol=s, name=s, value=1, change_pct=0)
                   for s in ("DJI", "SPX", "IXIC", "NDX", "SOX")]
        sectors = aggregate_sectors(_mk_members(), _mk_quotes())
        # 板块等权涨跌：信息技术 (2+(-1)+5)/3=+2.0 → 2涨1跌；能源 (-3+1)/2=-1.0 → 1涨1跌
        s = compose_summary(indices, sectors, as_of="2026-09-02")
        self.assertEqual(s.as_of, "2026-09-02")
        self.assertEqual([i.symbol for i in s.indices], ["DJI", "SPX", "IXIC"])
        self.assertEqual(s.advancers, 3)   # AAPL / NVDA / CVX
        self.assertEqual(s.decliners, 2)   # MSFT / XOM
        self.assertEqual(s.unchanged, 0)
        self.assertEqual(s.breadth_scope, "标普500成分口径")
        # 仅 2 板块时 gainers/losers 允许重叠，并集须恰好覆盖两板块
        self.assertEqual({g.name for g in s.top_gainers} | {l.name for l in s.top_losers},
                         {"信息技术", "能源"})
        self.assertTrue(s.updated_at)

    def test_top_gainers_losers_disjoint_and_ordered(self):
        # 造 6 个板块：gainers = 前3 降序；losers = 后3 按跌幅升序（最大跌幅在前）
        sectors = [UsSector(name=f"S{i}", change_pct=pct, leading_symbol="",
                            constituent_count=10)
                   for i, pct in enumerate([5.0, 4.0, 3.0, -1.0, -2.0, -3.0])]
        s = compose_summary([], sectors, "2026-09-02")
        self.assertEqual([g.name for g in s.top_gainers], ["S0", "S1", "S2"])
        self.assertEqual([l.name for l in s.top_losers], ["S5", "S4", "S3"])

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_data.py -v`
Expected: 新增 FAIL（`ImportError: cannot import name 'aggregate_sectors'`）。

- [ ] **Step 3: 实现聚合**

在 `us_data.py` 追加：

```python
def aggregate_sectors(members, quotes) -> list:
    """成员按 GICS 中文板块等权聚合。缺失行情的成员剔除，不计入任何统计。"""
    quote_by_symbol = {q.symbol: q for q in quotes}
    groups = {}
    for m in members:
        q = quote_by_symbol.get(m.symbol)
        if q is None:
            continue  # 无有效行情（停牌/退市/拉取失败）——不计入，避免假数据
        groups.setdefault(m.sector_cn, []).append((m, q))

    sectors = []
    for cn in us_universe.get_sector_cns():
        rows = groups.get(cn)
        if not rows:
            continue
        pcts = [q.change_pct for _, q in rows]
        avg = sum(pcts) / len(pcts)
        leader = max(rows, key=lambda r: r[1].change_pct)
        _, lq = leader
        advancers = sum(1 for p in pcts if p > 0)
        decliners = sum(1 for p in pcts if p < 0)
        sectors.append(UsSector(
            name=cn,
            name_en=us_universe.GICS_CN_TO_EN[cn],
            change_pct=round(avg, 4),
            leading_symbol=lq.symbol,
            leading_name=lq.name,
            leading_change_pct=round(lq.change_pct, 4),
            advancers=advancers,
            decliners=decliners,
            constituent_count=len(pcts),
            method="equal_weight",
        ))
    return sorted(sectors, key=lambda s: s.change_pct, reverse=True)


def sector_constituents(members, quotes, sector_cn: str) -> list:
    """板块成分按涨跌幅降序（用于右栏下钻）。"""
    quote_by_symbol = {q.symbol: q for q in quotes}
    rows = [(m, quote_by_symbol[m.symbol]) for m in members
            if m.sector_cn == sector_cn and m.symbol in quote_by_symbol]
    return [q for _, q in sorted(rows, key=lambda r: r[1].change_pct, reverse=True)]


def compose_summary(indices, sectors, as_of: Optional[str]):
    """合成 UsSummary：3 大指数 + 成分口径广度 + 领涨/领跌 Top3。"""
    from datetime import datetime
    major = {i.symbol: i for i in indices}
    indices_3 = [major[s] for s in _MAJOR_INDEX_SYMBOLS if s in major]
    advancers = sum(s.advancers for s in sectors)
    decliners = sum(s.decliners for s in sectors)
    unchanged = sum(s.constituent_count for s in sectors) - advancers - decliners
    return UsSummary(
        as_of=as_of or "",
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        indices=indices_3,
        advancers=advancers,
        decliners=decliners,
        unchanged=unchanged,
        top_gainers=sectors[:3],
        top_losers=sectors[-3:][::-1] if sectors else [],
    )
```

（文件顶部 import 增加 `from app.services import us_universe`。注意 `us_universe.GICS_CN_TO_EN` 已导出。）

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_data.py -v`
Expected: 全部 PASS。校验 `aggregate_sectors` 返回顺序：Energy=-1.0 出现在末位等。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/us_data.py backend/tests/test_us_data.py
git commit -m "feat(us): GICS 板块等权聚合与复盘概览合成"
```

---

## Task 6: 美股快照缓存（按 as_of 判定，非 300s TTL）

**Files:**
- Create: `backend/app/services/us_cache.py`
- Test: `backend/tests/test_us_cache.py`

**Interfaces:**
- Consumes: `us_universe.load_us_constituents`、`us_data.fetch_index_quotes/fetch_index_asof/fetch_constituent_quotes/aggregate_sectors/compose_summary`。
- Produces:
  - `us_cache.UsCacheSnapshot`（dataclass：`indices: list`, `sectors: list`, `quote_map: dict[str, UsConstituent]`, `as_of: str | None`, `updated_at: float`）。
  - `us_cache.get_us_snapshot(force: bool = False) -> UsCacheSnapshot | None`（线程安全）。
  - `us_cache._decide_refresh(cache, as_of, now, force, probe_ttl) -> str`（纯决策函数：返回 `"sync_full" | "probe" | "hit"`，便于单测）。
  - `us_cache.reset_cache()`（测试用）。

**缓存策略（对应 Spec §5.2，关键：不能照抄 A 股 300s 高频）**
- 全量数据（503 成分 × ~1s / 并发 16 ≈ 40-60s）只应在**数据日期变化或首次**时同步拉取。
- `as_of`（成分 bar 日期众数）即"已入库美东交易日"。缓存命中期间，用**轻量 1 请求**探测 `.INX` 的 as_of：
  - 探测结果 ≠ 缓存 as_of（说明新浪已写入新交易日）→ 同步全量重拉。
  - 探测结果 == 缓存 as_of 或探测失败 → 继续用缓存（失败静默，不打断用户）。
- 探测不是每次请求都发：`PROBE_TTL = 300s` 内只探测一次；`MIN_AGE_BEFORE_PROBE = 60s`。
- 全量重拉失败：保留旧缓存并打印；无旧缓存返回 `None`（路由层转 503）。

- [ ] **Step 1: 写失败测试**

`backend/tests/test_us_cache.py`：

```python
import unittest
from unittest.mock import patch

from app.services import us_cache
from app.services.us_cache import _decide_refresh, get_us_snapshot, reset_cache
from app.models.schemas import UsConstituent, UsIndexQuote


class DecideRefreshTest(unittest.TestCase):
    """纯决策函数：force / as_of 变化 / TTL 组合下的动作选择。"""

    def test_first_ever_call_is_sync_full(self):
        cache = {"as_of": None, "time": 0.0, "indices": [], "sectors": []}
        self.assertEqual(_decide_refresh(cache, as_of="2026-09-02", now=100.0,
                                         force=False, probe_ttl=300.0), "sync_full")

    def test_cache_fresh_hit_without_probe(self):
        cache = {"as_of": "2026-09-02", "time": 50.0, "sectors": ["x"]}
        # now=100，距上次 50s < probe 触发下限；直接命中
        self.assertEqual(_decide_refresh(cache, as_of=None, now=100.0,
                                         force=False, probe_ttl=300.0), "hit")

    def test_after_probe_ttl_probes(self):
        cache = {"as_of": "2026-09-02", "time": 10.0, "sectors": ["x"]}
        # now=400，距上次 390s >= 探测间隔；需要 probe
        self.assertEqual(_decide_refresh(cache, as_of=None, now=400.0,
                                         force=False, probe_ttl=300.0), "probe")

    def test_asof_changed_triggers_full(self):
        cache = {"as_of": "2026-09-02", "time": 10.0, "sectors": ["x"]}
        self.assertEqual(_decide_refresh(cache, as_of="2026-09-03", now=400.0,
                                         force=False, probe_ttl=300.0), "sync_full")

    def test_force_always_full(self):
        cache = {"as_of": "2026-09-03", "time": 999.0, "sectors": ["x"]}
        self.assertEqual(_decide_refresh(cache, as_of="2026-09-03", now=1000.0,
                                         force=True, probe_ttl=300.0), "sync_full")


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        reset_cache()

    def test_first_call_builds_snapshot(self):
        members = _fake_members()
        with patch.object(us_cache, "_get_ak", return_value=object()), \
                patch.object(us_cache.us_data, "fetch_index_asof", return_value="2026-09-02"), \
                patch.object(us_cache.us_data, "fetch_index_quotes", side_effect=_fake_indices), \
                patch.object(us_cache.us_data, "fetch_constituent_quotes", side_effect=_fake_constituents), \
                patch.object(us_cache.us_universe, "load_us_constituents", return_value=members):
            snap = get_us_snapshot()
        self.assertEqual(snap.as_of, "2026-09-02")
        self.assertEqual(len(snap.quote_map), 3)
        self.assertEqual([s.name for s in snap.sectors],
                         ["信息技术", "能源"])  # +1.0 vs -1.5 降序
        self.assertEqual([i.symbol for i in snap.indices], ["DJI", "SPX", "IXIC"])

    def test_refresh_failure_returns_stale_and_second_hit_reuses(self):
        members = _fake_members()
        calls = {"n": 0}

        def flaky_constituents(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                return _fake_constituents(None)
            raise RuntimeError("network down")

        with patch.object(us_cache, "_get_ak", return_value=object()), \
                patch.object(us_cache.us_data, "fetch_index_asof", return_value="2026-09-02"), \
                patch.object(us_cache.us_data, "fetch_index_quotes", side_effect=_fake_indices), \
                patch.object(us_cache.us_data, "fetch_constituent_quotes", side_effect=flaky_constituents), \
                patch.object(us_cache.us_universe, "load_us_constituents", return_value=members), \
                patch.object(us_cache.time, "time", return_value=100.0):
            snap1 = get_us_snapshot()            # 首次成功
            snap2 = get_us_snapshot()            # 命中缓存，不触发重拉
        self.assertEqual(snap1.as_of, "2026-09-02")
        self.assertEqual(calls["n"], 1)
        self.assertIs(snap2, snap1)


def _fake_members():
    from app.services.us_universe import UsUniverseMember
    return [
        UsUniverseMember("AAPL", "Apple", "Information Technology"),
        UsUniverseMember("MSFT", "Microsoft", "Information Technology"),
        UsUniverseMember("XOM", "Exxon", "Energy"),
    ]


def _fake_indices(*a, **k):
    return [UsIndexQuote(symbol="DJI", name="道琼斯", value=1, change_pct=0),
            UsIndexQuote(symbol="SPX", name="标普500", value=1, change_pct=0),
            UsIndexQuote(symbol="IXIC", name="纳斯达克", value=1, change_pct=0)]


def _fake_constituents(members, **k):
    specs = {"AAPL": 1.0, "MSFT": 2.0, "XOM": -1.5}
    quotes = [UsConstituent(symbol=s, name=s, price=100 + p, change_amount=p, change_pct=p)
              for s, p in specs.items()]
    return quotes, "2026-09-02"


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_cache.py -v`
Expected: FAIL（`ModuleNotFoundError`）。

- [ ] **Step 3: 实现缓存**

`backend/app/services/us_cache.py`：

```python
"""美股数据快照缓存 —— 按数据日期(as_of)判定，不是 300s 高频 TTL。

成分行情是一次 500 请求 / ~1 分钟的代价换来的，不能像 A 股板块那样
每 5 分钟重拉。策略：
- 首次访问或探测到新浪已入库"新交易日"(as_of 变化) → 同步全量重拉一次；
- 其余时间内命中缓存，且仅每隔 PROBE_TTL 发 1 个轻量探测请求确认 as_of 未变；
- 全量重拉失败 → 保留旧快照并打印（首次失败才返回 None）。
"""
import threading
import time

from app.services import us_data, us_universe
from app.services.stock_data import _get_ak
from app.models.schemas import UsConstituent

PROBE_TTL = 300.0      # 探测间隔（秒）
MIN_AGE = 60.0         # 距上次刷新不足此值直接命中，不发探测

_cache = {
    "as_of": None,      # str | None，最近已入库美东交易日
    "indices": [],      # list[UsIndexQuote]
    "sectors": [],      # list[UsSector]（降序）
    "quote_map": {},    # dict[symbol, UsConstituent]
    "time": 0.0,        # 最近一次全量刷新时刻
    "last_probe": 0.0,  # 最近一次探测时刻
    "loading": False,
}
_lock = threading.Lock()


def reset_cache():
    """清空缓存（测试用）。"""
    with _lock:
        for k in ("as_of", "indices", "sectors", "quote_map",
                  "time", "last_probe", "loading"):
            _cache[k] = None if k == "as_of" else ({} if k == "quote_map"
                                                   else ([] if k in ("indices", "sectors")
                                                         else 0.0 if k in ("time", "last_probe")
                                                         else False))


def _decide_refresh(cache, as_of, now, force, probe_ttl=PROBE_TTL):
    """决策下一步动作：'sync_full'（同步全量重拉）| 'probe'（发轻量探测）| 'hit'（直接命中）。"""
    if force or cache["as_of"] is None:
        return "sync_full"
    age = now - cache["time"]
    if age < MIN_AGE:
        return "hit"
    if as_of is not None and as_of != cache["as_of"]:
        return "sync_full"   # 已探测且确认有新交易日数据
    if now - cache["last_probe"] >= probe_ttl:
        return "probe"
    return "hit"


def _full_refresh() -> None:
    """拉全量：指数 + 全部成分并聚合成 sectors/quote_map。失败抛异常由调用方兜底。"""
    ak = _get_ak()
    members = us_universe.load_us_constituents()
    quotes, as_of = us_data.fetch_constituent_quotes(members, ak=ak)
    if not quotes or not as_of:
        raise RuntimeError("美股成分行情拉取为空")
    indices = us_data.fetch_index_quotes(ak=ak)
    sectors = us_data.aggregate_sectors(members, quotes)
    _cache["indices"] = indices
    _cache["sectors"] = sectors
    _cache["quote_map"] = {q.symbol: q for q in quotes}
    _cache["as_of"] = as_of
    _cache["time"] = time.time()
    print(f"[us缓存] 全量刷新完成 {as_of}，成分 {len(quotes)}，板块 {len(sectors)}")


def get_us_snapshot(force: bool = False):
    """返回当前快照（线程安全）。首次/新交易日同步全量；否则命中，必要时后台探测。"""
    now = time.time()
    decision = _decide_refresh(_cache, None, now, force)
    if decision == "sync_full":
        with _lock:
            try:
                _full_refresh()
            except Exception as e:
                print(f"[us缓存] 全量刷新失败: {e}")
                if _cache["as_of"] is None:
                    return None
        return _snapshot()
    if decision == "probe":
        # 探测 as_of（1 个轻请求）。失败静默，保持缓存。
        probe_asof = None
        try:
            probe_asof = us_data.fetch_index_asof()
        except Exception as e:
            print(f"[us缓存] as_of 探测失败: {e}")
        with _lock:
            _cache["last_probe"] = time.time()
            if probe_asof is not None and probe_asof != _cache["as_of"]:
                # 数据日期已更新：站到同步刷新一侧
                try:
                    _full_refresh()
                except Exception as e:
                    print(f"[us缓存] 数据更新后全量刷新失败: {e}")
    return _snapshot()


def _snapshot():
    with _lock:
        return UsCacheSnapshot(
            indices=list(_cache["indices"]),
            sectors=list(_cache["sectors"]),
            quote_map=dict(_cache["quote_map"]),
            as_of=_cache["as_of"],
            updated_at=_cache["time"],
        )


class UsCacheSnapshot:
    """线程快照值对象（不可变语义：返回副本）。"""
    __slots__ = ("indices", "sectors", "quote_map", "as_of", "updated_at")

    def __init__(self, indices, sectors, quote_map, as_of, updated_at):
        self.indices = indices
        self.sectors = sectors
        self.quote_map = quote_map
        self.as_of = as_of
        self.updated_at = updated_at


def clear_cache_for_tests():
    reset_cache()
```

> 说明：`_decide_refresh` 里 `MIN_AGE` 命中逻辑与测试对齐（`age=50 < 60 → hit`、`age=390 ≥ MIN_AGE` 且距上次探测 390 ≥ 300 → probe）。首个测试用 `now=100.0`、`cache.time=50.0` 得 age=50 → hit；第三例 `now=400`、`time=10` → probe。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_cache.py -v`
Expected: 全部 PASS（决策 5 + 快照 2）。`time` 在测试里被 monkeypatch 以固定 100.0，`_full_refresh` 内 `time.time()` 也是 100.0，命中逻辑一致。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/us_cache.py backend/tests/test_us_cache.py
git commit -m "feat(us): 按美东数据日期判定的美股快照缓存"
```

---

## Task 7: `/api/us` REST 路由 + 注册

**Files:**
- Create: `backend/app/routes/us.py`
- Modify: `backend/app/main.py`（注册 router）
- Test: `backend/tests/test_us_routes.py`

**Interfaces:**
- Consumes: `us_cache.get_us_snapshot`、`us_data.compose_summary/sector_constituents`、`us_universe.load_us_constituents`。
- Produces（供前端 Task F1）：
  - `GET /api/us/summary` → `UsSummary`（503 当无数据）。
  - `GET /api/us/sectors` → `List[UsSector]`（503 当无数据）。
  - `GET /api/us/sectors/{name}/constituents` → `List[UsConstituent]`（name 为 URL 编码的中文板块名；无数据/未知板块 → 404）。
  - `GET /api/us/ai-summary`（SSE，Task 8 实现内容，本 Task 先建壳返回静态兜底）。

- [ ] **Step 1: 写失败测试**

`backend/tests/test_us_routes.py`（用 FastAPI `TestClient` + monkeypatch service；不触真实网络）：

```python
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import UsConstituent, UsIndexQuote, UsSector

client = TestClient(app)


def _fake_snapshot():
    class Snap:
        as_of = "2026-09-02"
        indices = [UsIndexQuote(symbol="DJI", name="道琼斯", value=53061.95, change_pct=0.56),
                   UsIndexQuote(symbol="SPX", name="标普500", value=4512.3, change_pct=0.72),
                   UsIndexQuote(symbol="IXIC", name="纳斯达克", value=14032.11, change_pct=1.18)]
        sectors = [UsSector(name="信息技术", change_pct=2.0, leading_symbol="NVDA",
                            leading_change_pct=5.0, advancers=2, decliners=1,
                            constituent_count=3),
                   UsSector(name="能源", change_pct=-1.5, leading_symbol="XOM",
                            leading_change_pct=-3.0, advancers=0, decliners=2,
                            constituent_count=2)]
        quote_map = {"AAPL": UsConstituent(symbol="AAPL", name="Apple", price=230.0,
                                           change_pct=0.877, change_amount=2.0)}
    return Snap()


class UsRoutesTest(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("app.routes.us.get_us_snapshot", return_value=_fake_snapshot())
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_summary_shape(self):
        r = client.get("/api/us/summary")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["as_of"], "2026-09-02")
        self.assertEqual([i["symbol"] for i in d["indices"]], ["DJI", "SPX", "IXIC"])
        self.assertEqual(d["advancers"], 2)
        self.assertEqual(d["decliners"], 3)
        self.assertEqual(d["breadth_scope"], "标普500成分口径")
        self.assertEqual([g["name"] for g in d["top_gainers"]], ["信息技术"])

    def test_sectors_sorted_desc(self):
        r = client.get("/api/us/sectors")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual([s["name"] for s in body], ["信息技术", "能源"])
        self.assertEqual(body[0]["method"], "equal_weight")

    def test_sector_constituents_returns_filtered_list(self):
        with patch("app.routes.us.load_us_constituents") as uni:
            uni.return_value = [type("M", (), {"symbol": "AAPL", "sector_cn": "信息技术",
                                               "name_en": "Apple"})()]
            r = client.get("/api/us/sectors/%E4%BF%A1%E6%81%AF%E6%8A%80%E6%9C%AF/constituents")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()[0]["symbol"], "AAPL")

    def test_unknown_sector_404(self):
        r = client.get("/api/us/sectors/%E4%B8%8D%E5%AD%98%E5%9C%A8/constituents")
        self.assertEqual(r.status_code, 404)

    def test_snapshot_none_503(self):
        with patch("app.routes.us.get_us_snapshot", return_value=None):
            self.assertEqual(client.get("/api/us/summary").status_code, 503)
            self.assertEqual(client.get("/api/us/sectors").status_code, 503)


if __name__ == "__main__":
    unittest.main()
```

（`TestClient(app)` 会触发 app 的 startup？`TestClient` 默认不运行 lifespan/on_event，但导入 `app.main` 会执行模块顶层 import（数据库 model 导入等）。若当前环境 `app.main` 导入即建引擎不连库，TestClient 请求不会触发 startup event，安全。若个别环境启动 DB 失败，可改为 `TestClient(app)` + 手动关 lifespan，参照现有 `tests/test_frontend_serving.py` 的处理。）

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_routes.py -v`
Expected: FAIL（`ModuleNotFoundError: app.routes.us`）。

- [ ] **Step 3: 实现路由**

`backend/app/routes/us.py`：

```python
"""美股复盘 API 路由（收盘口径，方案 B 聚合）。"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List

from app.services import us_cache, us_data, us_universe
from app.models.schemas import UsConstituent, UsSector, UsSummary

router = APIRouter(prefix="/api/us", tags=["美股"])

# 摘要/卡片的静态口径说明（产品文案，后端随文档常量带出）
BREADTH_SCOPE = "标普500成分口径"


@router.get("/summary", response_model=UsSummary, summary="美股收盘复盘概览")
async def get_us_summary():
    """Dashboard 卡片与页面摘要区共用：3 指数 + 成分广度 + 领涨/领跌板块。"""
    snap = us_cache.get_us_snapshot()
    if not snap:
        raise HTTPException(status_code=503, detail="美股数据获取失败，请稍后重试")
    summary = us_data.compose_summary(snap.indices, snap.sectors, snap.as_of)
    summary.breadth_scope = BREADTH_SCOPE
    return summary


@router.get("/sectors", response_model=List[UsSector], summary="美股 GICS 板块涨跌榜")
async def get_us_sectors():
    """11 个 GICS 板块等权涨跌，按涨跌幅降序（领涨在上）。"""
    snap = us_cache.get_us_snapshot()
    if not snap:
        raise HTTPException(status_code=503, detail="美股数据获取失败，请稍后重试")
    return snap.sectors


@router.get("/sectors/{name}/constituents", response_model=List[UsConstituent],
            summary="板块成分股")
async def get_us_sector_constituents(name: str):
    """板块成分按涨跌幅降序（成分 = 标普500 中该 GICS 板块成员）。"""
    if name not in us_universe.get_sector_cns():
        raise HTTPException(status_code=404, detail="未知板块")
    snap = us_cache.get_us_snapshot()
    if not snap:
        raise HTTPException(status_code=503, detail="美股数据获取失败，请稍后重试")
    members = us_universe.load_us_constituents()
    stocks = us_data.sector_constituents(members, list(snap.quote_map.values()), name)
    return stocks


@router.get("/ai-summary", summary="AI 美股一句话复盘（流式）")
async def get_us_ai_summary():
    """美股复盘一句话主线，SSE 流式；实现在 Task 8 接入。"""
    from app.services.ai_analyst import analyze_us_market_stream
    from app.services.sse import format_sse_data

    async def event_stream():
        yield format_sse_data("🤖 AI 正在复盘美股...")
        snap = us_cache.get_us_snapshot()
        if not snap:
            yield format_sse_data("❌ 美股数据获取失败，请稍后重试")
            yield format_sse_data("[DONE]")
            return
        async for chunk in analyze_us_market_stream(snap):
            yield format_sse_data(chunk)
        yield format_sse_data("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "Connection": "keep-alive",
                                      "X-Accel-Buffering": "no"})
```

`backend/app/main.py`：import 与注册追加（与现有 board_router 相邻）：

```python
from app.routes.us import router as us_router
...
app.include_router(us_router)
```

（路由引用 `analyze_us_market_stream` / `format_sse_data` 属 Task 8 产物，Task 7 跑测试时该函数不存在会 ImportError —— 见下一步调整。）

- [ ] **Step 4: 运行确认通过**

Task 8 前 `ai-summary` 依赖未实现，本步先建一个占位实现供测试通过（Task 8 再替换为真实 AI 流）。在 `backend/app/services/ai_analyst.py` 末尾临时追加并提交到 Task 7：

```python
async def analyze_us_market_stream(snapshot):
    """美股一句话复盘。Task 8 将替换为真实 LLM 流式生成。"""
    if snapshot is None or not snapshot.sectors:
        yield "今日美股主线暂不明朗（数据不足）。"
        return
    top = snapshot.sectors[0]
    yield (f"今日领涨板块 {top.name}（{top.change_pct:+.2f}%，领涨 {top.leading_symbol} "
           f"{top.leading_change_pct:+.2f}%）；标普500成分等权口径，非投资建议。")
```

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_routes.py tests/test_us_schemas.py tests/test_us_data.py tests/test_us_cache.py tests/test_us_universe.py -v`
Expected: 全部 PASS（占位 ai-summary 也让 summary/sectors/constituents 用例通过）。

- [ ] **Step 5: 提交**

```bash
git add backend/app/routes/us.py backend/app/main.py backend/app/services/ai_analyst.py backend/tests/test_us_routes.py
git commit -m "feat(us): /api/us summary/sectors/constituents/ai-summary 路由与注册"
```

---

## Task 8: AI 一句话主线（归因禁令 + SSE）

**Files:**
- Modify: `backend/app/services/ai_analyst.py`（替换占位 `analyze_us_market_stream` + 新增 prompt/system 常量）
- Test: `backend/tests/test_us_ai.py`（新增）

**Interfaces:**
- Consumes: `us_cache.UsCacheSnapshot`、`settings.ai_available`、`_get_client`（anomaly: 与 `analyze_market_stream` 相同用法）。
- Produces: `ai_analyst._build_us_market_prompt(snapshot) -> str`；`ai_analyst.analyze_us_market_stream(snapshot) -> AsyncGenerator[str, None]`；`ai_analyst.US_MARKET_SYSTEM_PROMPT`。

**AI 约束（Global Constraint 3 落地为 system prompt）：**
- 只陈述输入数据里的事实；禁止归因词（由于/受…影响/因为/因此/导致）；每条判断可对照 prompt 中的可核对数字；数据不足给静态兜底句；结尾固定风险句；注明标普500成分口径。

- [ ] **Step 1: 写失败测试**

`backend/tests/test_us_ai.py`：

```python
import unittest

from app.services import ai_analyst
from app.services.ai_analyst import US_MARKET_SYSTEM_PROMPT, _build_us_market_prompt
from app.models.schemas import UsSector


def _snap():
    class S:
        as_of = "2026-09-02"
        indices = []
        sectors = [UsSector(name="信息技术", change_pct=2.0, leading_symbol="NVDA",
                            leading_name="NVIDIA", leading_change_pct=5.0,
                            advancers=2, decliners=1, constituent_count=3),
                   UsSector(name="能源", change_pct=-1.5, leading_symbol="XOM",
                            leading_change_pct=-3.0, advancers=0, decliners=2,
                            constituent_count=2)]
    return S()


class UsAiTest(unittest.TestCase):
    def test_system_prompt_bans_attribution_and_requires_fallback(self):
        text = US_MARKET_SYSTEM_PROMPT
        for bad in ("由于", "受", "影响", "因为", "因此", "导致"):
            self.assertIn(bad, text)   # 禁令以"不得使用 XX"形式出现，故禁令词本身在 prompt 中
        self.assertIn("标普500", text)

    def test_prompt_injects_verifiable_numbers(self):
        prompt = _build_us_market_prompt(_snap())
        self.assertIn("信息技术", prompt)
        self.assertIn("+2.00%", prompt)
        self.assertIn("NVDA", prompt)
        self.assertIn("2026-09-02", prompt)

    def test_ai_unavailable_returns_static_guard(self):
        async def run():
            out = []
            with unittest.mock.patch.object(ai_analyst.settings, "ai_available", False):
                async for chunk in ai_analyst.analyze_us_market_stream(_snap()):
                    out.append(chunk)
            return "".join(out)

        text = _run_sync(run())
        self.assertIn("AI 服务暂不可用", text)

    def test_fallback_sentence_on_insufficient_data(self):
        prompt = _build_us_market_prompt(None)
        self.assertIn("主线暂不明朗", prompt)


def _run_sync(awaitable):
    import asyncio
    return asyncio.run(awaitable)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_ai.py -v`
Expected: FAIL（`US_MARKET_SYSTEM_PROMPT` 未定义 / prompt 不含预期数字）。

- [ ] **Step 3: 实现 AI 流（替换占位）**

在 `ai_analyst.py` 中，`analyze_market_stream` 之后新增（并把 Task 7 临时占位函数整体替换为下述实现）：

```python
US_MARKET_SYSTEM_PROMPT = """你是一名美股盘后复盘分析师，为中文投资者做"美股收盘复盘一句话"。

硬性规则（违反即不合格）：
1. 只用中文，输出 40-90 字一段话。
2. 只陈述下面数据里的事实，禁止猜测或编造原因；不得使用"由于 / 受…影响 / 因为 / 因此 / 导致 / 表明"等归因、因果表述。
3. 每条强弱判断必须能对照数据中的可核对数字（指数点位与涨跌幅、板块等权涨跌幅、领涨领跌成分 ticker 与其涨跌幅）。
4. 涨跌范围只限于标普500成分等权口径，不得写成全市场结论；数据不足或主线不明时，直接写"今日美股主线暂不明朗"。
5. 结尾必须追加一句："（标普500成分等权口径，非投资建议。）"
"""


def _build_us_market_prompt(snapshot) -> str:
    """把美股快照转成可核对的事实清单。snapshot 为 None/空时给出兜底引导。"""
    if snapshot is None or not getattr(snapshot, "sectors", None):
        return ("请直接输出：今日美股主线暂不明朗。（标普500成分等权口径，非投资建议。）\n"
                "（当前无可用复盘数据，不要编造板块或个股表现。）")
    lines = [f"【数据日期】美东 {snapshot.as_of}（收盘）"]
    for i in snapshot.indices:
        lines.append(f"- 指数 {i.name}：{i.value:.2f} 点 {i.change_pct:+.2f}%")
    gainers = [s for s in snapshot.sectors[:3]]
    losers = [s for s in snapshot.sectors[-3:]][::-1]
    lines.append("【领涨板块】" + "；".join(
        f"{s.name} {s.change_pct:+.2f}%（领涨 {s.leading_symbol} {s.leading_change_pct:+.2f}%）"
        for s in gainers) if gainers else "无")
    lines.append("【领跌板块】" + "；".join(
        f"{s.name} {s.change_pct:+.2f}%（领跌 {s.leading_symbol} {s.leading_change_pct:+.2f}%）"
        for s in losers) if losers else "无")
    adv = sum(s.advancers for s in snapshot.sectors)
    dec = sum(s.decliners for s in snapshot.sectors)
    lines.append(f"【成分广度】标普500成分口径：上涨 {adv} / 下跌 {dec}")
    return "\n".join(lines)


async def analyze_us_market_stream(snapshot) -> "AsyncGenerator[str, None]":
    """流式生成美股复盘一句话（SSE 用）。"""
    if not settings.ai_available:
        yield "⚠️ AI 服务暂不可用：未配置 API Key。"
        return
    try:
        user_prompt = _build_us_market_prompt(snapshot)
        client = _get_client()
        async with client.messages.stream(
            model=settings.ARK_MODEL,
            max_tokens=200,
            system=US_MARKET_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"\n\n❌ AI 复盘出错：{str(e)}"
        print(f"AI 美股复盘错误: {e}")
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/test_us_ai.py tests/test_us_routes.py -v`
Expected: 全部 PASS。手动对 ai-summary 做一次 curl 冒烟（可选，需网络与 API key；不配 key 时应输出 ⚠️ 首块 + [DONE]）。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/ai_analyst.py backend/tests/test_us_ai.py
git commit -m "feat(us): 美股一句话复盘 LLM 流（只陈述不归因 + 静态兜底）"
```

---

## Task F1: 前端 API 封装 `api/us.js`

**Files:**
- Create: `frontend/src/api/us.js`
- Test: `frontend/tests/us-api-contract.test.js`

**Interfaces:**
- Produces: `getUsSummary() -> Promise<UsSummary>`、`getUsSectors() -> Promise<UsSector[]>`、`getUsSectorStocks(name) -> Promise<UsConstituent[]>`、`getUsAiSummary(onMessage, onDone, onError) -> EventSource`。

- [ ] **Step 1: 写失败契约测试**

`frontend/tests/us-api-contract.test.js`（沿用仓库「文本契约」风格，读源码断言）：

```js
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { readFile } = require('node:fs/promises')
const { resolve } = require('node:path')

const SRC = resolve(__dirname, '../src')

async function readApi() {
  return readFile(resolve(SRC, 'api/us.js'), 'utf8')
}

test('api/us.js 导出四个美股接口函数', async () => {
  const code = await readApi()
  for (const fn of ['getUsSummary', 'getUsSectors', 'getUsSectorStocks', 'getUsAiSummary']) {
    assert.match(code, new RegExp(`export (async )?function ${fn}|export const ${fn}`))
  }
})

test('REST 接口路径与返回约定', async () => {
  const code = await readApi()
  assert.match(code, /\/us\/summary/)
  assert.match(code, /\/us\/sectors/)
  assert.match(code, /sectors\/\$\{name\}|sectors\/\$\{encodeURIComponent/)
  assert.match(code, /encodeURIComponent/)
  assert.match(code, /\.then\(res => res\.data\)/)
})

test('SSE 封装遵循 [DONE] 与 EventSource 约定', async () => {
  const code = await readApi()
  assert.match(code, /EventSource\(/)
  assert.match(code, /\/us\/ai-summary/)
  assert.match(code, /'\[DONE\]'|"\[DONE\]"/)
  assert.match(code, /eventSource\.close\(\)/)
  assert.match(code, /return eventSource/)
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && node --test tests/us-api-contract.test.js`
Expected: FAIL（文件不存在读不到 / 断言不匹配）。

- [ ] **Step 3: 实现 API**

`frontend/src/api/us.js`（仿 `api/stock.js` 的板块函数 + SSE 封装；先读该文件顶部 `import http from './http'`）：

```js
// 美股复盘 API（收盘口径；对应后端 /api/us）
import http from './http'

// GET /api/us/summary —— Dashboard 卡与页面摘要区共用
export function getUsSummary() {
  return http.get('/us/summary').then(res => res.data)
}

// GET /api/us/sectors —— 11 个 GICS 板块涨跌榜（后端已按涨幅降序）
export function getUsSectors() {
  return http.get('/us/sectors').then(res => res.data)
}

// GET /api/us/sectors/{name}/constituents —— 板块成分按涨跌幅降序
export function getUsSectorStocks(name) {
  return http.get(`/us/sectors/${encodeURIComponent(name)}/constituents`).then(res => res.data)
}

// GET /api/us/ai-summary —— AI 一句话复盘（SSE），[DONE] 收尾
export function getUsAiSummary(onMessage, onDone, onError) {
  const eventSource = new EventSource('/api/us/ai-summary')
  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onDone && onDone()
      return
    }
    onMessage && onMessage(event.data)
  }
  eventSource.onerror = () => {
    eventSource.close()
    onError && onError(new Error('美股 AI 摘要连接中断'))
  }
  return eventSource
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && node --test tests/us-api-contract.test.js`
Expected: 3 个 PASS。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/us.js frontend/tests/us-api-contract.test.js
git commit -m "feat(us): 前端美股 API 封装与契约测试"
```

---

## Task F2: composables（useUsMarket + useUsCard）

**Files:**
- Create: `frontend/src/composables/useUsMarket.js`
- Create: `frontend/src/composables/useUsCard.js`
- Test: `frontend/tests/us-market-contract.test.js`（先只覆盖 composable 部分，F4 补组件断言）

**Interfaces:**
- Produces:
  - `useUsMarket()` → `{ summarySection, sectorsSection, aiText, aiLoading, aiError, loadSummary, loadSectors, generateAiSummary, closeAiSource }`；`summarySection/sectorsSection` 为 `useAsyncSection` 实例（`.data/.state/.run/.retry/.isLoading` 等）。
  - `useUsCard()` → `{ cardData, cardLoading, cardError, loadCard, retryCard }`（只拉 `getUsSummary`）。

- [ ] **Step 1: 写失败契约测试（本步追加到 us-market-contract.test.js）**

```js
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { readFile } = require('node:fs/promises')
const { resolve } = require('node:path')

const SRC = resolve(__dirname, '../src')

async function read(p) { return readFile(resolve(SRC, p), 'utf8') }

test('useUsMarket 用两条 useAsyncSection + SSE 摘要', async () => {
  const code = await read('composables/useUsMarket.js')
  assert.match(code, /useAsyncSection\(getUsSummary/)
  assert.match(code, /useAsyncSection\(getUsSectors/)
  assert.match(code, /getUsAiSummary\(/)
  assert.match(code, /closeAiSource|eventSource\.close/)
})

test('useUsMarket 导出摘要/榜单/AI 状态', async () => {
  const code = await read('composables/useUsMarket.js')
  for (const key of ['summarySection', 'sectorsSection', 'generateAiSummary']) {
    assert.match(code, new RegExp(key))
  }
})

test('useUsCard 只消费 summary 接口', async () => {
  const code = await read('composables/useUsCard.js')
  assert.match(code, /useAsyncSection\(getUsSummary/)
  assert.doesNotMatch(code, /getUsSectors/)
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && node --test tests/us-market-contract.test.js`
Expected: FAIL。

- [ ] **Step 3: 实现 composables**

写实现前先 `Read frontend/src/composables/useAsyncSection.js`（确认 `.run/.retry/.data/.isLoading/.isError` 实际成员名与是否已内置 requestId 防串号），再看现有页面（`frontend/src/views/Dashboard.vue` 或 `frontend/src/views/BoardMonitor.vue`）里它被调用的真实写法，照其拼装状态与 SSE 拼接。

`frontend/src/composables/useUsCard.js`：

```js
// Dashboard「美股收盘」卡片数据：只消费 /api/us/summary，无轮询（收盘复盘）
import { useAsyncSection } from './useAsyncSection'
import { getUsSummary } from '../api/us'

export function useUsCard() {
  const card = useAsyncSection(getUsSummary, { initialData: null })
  return {
    cardData: card.data,
    cardLoading: card.isLoading,
    cardError: card.isError,
    loadCard: card.run,
    retryCard: card.retry,
  }
}
```

`frontend/src/composables/useUsMarket.js`：

```js
// 美股复盘页数据编排：摘要 + 板块榜（useAsyncSection）+ AI 一句话（SSE）
import { useAsyncSection } from './useAsyncSection'
import { getUsAiSummary, getUsSectors, getUsSummary } from '../api/us'

export function useUsMarket() {
  const summarySection = useAsyncSection(getUsSummary, { initialData: null })
  const sectorsSection = useAsyncSection(getUsSectors, { initialData: [] })

  const aiText = ref('')
  const aiLoading = ref(false)
  const aiError = ref(false)
  let aiSource = null
  let aiRequestId = 0

  async function generateAiSummary() {
    const requestId = ++aiRequestId
    if (aiSource) { aiSource.close(); aiSource = null }
    aiLoading.value = true
    aiError.value = false
    aiText.value = ''
    try {
      aiSource = getUsAiSummary(
        (chunk) => { if (requestId === aiRequestId) aiText.value += chunk },
        () => { if (requestId === aiRequestId) aiLoading.value = false },
        () => { if (requestId === aiRequestId) { aiLoading.value = false; aiError.value = true } },
      )
    } catch (e) {
      aiLoading.value = false
      aiError.value = true
    }
  }

  function closeAiSource() {
    aiRequestId += 1
    if (aiSource) { aiSource.close(); aiSource = null }
    aiLoading.value = false
  }

  return {
    summarySection, sectorsSection,
    aiText, aiLoading, aiError,
    loadSummary: summarySection.run,
    loadSectors: sectorsSection.run,
    generateAiSummary, closeAiSource,
  }
}
```

（`useAsyncSection` 的 loader 接收单参 fetcher；若其签名需 `run(args)` 带参请按 `useDashboardMarket.js` 实际用法调整——加载前 `Read` 确认。）

> 注意：`ref` 需 `import { ref } from 'vue'`。若 `useDashboardMarket.js` 不暴露与上述一致的 API，执行者应以其为最终权威微调本文件，但**保持上述导出契约不变**（契约测试只认名字）。

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && node --test tests/us-market-contract.test.js`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/composables/useUsMarket.js frontend/src/composables/useUsCard.js frontend/tests/us-market-contract.test.js
git commit -m "feat(us): 美股页/Dashboard 卡数据编排 composables"
```

---

## Task F3: 展示组件（UsIndexStrip / UsSectorTable / UsSectorDetailPanel / UsSnapshotCard）+ MarketAiSummary label 化

**Files:**
- Create: `frontend/src/components/us/UsIndexStrip.vue`
- Create: `frontend/src/components/us/UsSectorTable.vue`
- Create: `frontend/src/components/us/UsSectorDetailPanel.vue`
- Create: `frontend/src/components/dashboard/UsSnapshotCard.vue`
- Modify: `frontend/src/components/dashboard/MarketAiSummary.vue`（加 `label` prop）
- Test: 本任务以「先读参照文件 + 手动冒烟」为主，契约断言集中在 Task F4/F6。

**Interfaces（组件契约，F4/F6 将按此断言）：**
- `UsIndexStrip.vue`：props `summary`(Object)。展示 3 指数（`summary.indices`，每个 `PriceDisplay`：`price=value`、`change=change_amount`、`changePercent=change_pct`），右侧 `MetricCell`「涨/跌」`advancers/decliners`；数字统一 `formatThousands/safeNumber`。
- `UsSectorTable.vue`：props `sectors`(Array)、`loading`、`error`、`selectedName`(String)；emits `select`(UsSector)、`retry`。**无分页/无搜索/无排序控件**（Global Constraint 4）。
- `UsSectorDetailPanel.vue`：props `visible`、`loading`、`error`、`mobile`(Boolean)、`board`(UsSector|null)、`stocks`(Array)；emits `close`、`retry`、`open-symbol`(symbol)。桌面 `SectionPanel` 常驻右栏，移动 `ElDrawer`(btt, size 100%)，容器切换仿 `board/BoardDetailPanel.vue`。
- `UsSnapshotCard.vue`：props `summary`(Object|null)、`loading`、`error`；emits `retry`、`open`、`sector`(sector name)。整体 `SectionPanel variant="flush"`，header 标题「美股收盘」+ `as_of` 小字 +「进入美股复盘」link。
- `MarketAiSummary.vue`：新增 `label = { type: String, default: 'AI 盘面结论' }` 替换写死文案，向后兼容。

- [ ] **Step 1: 阅读参照文件**

Read（各自开写前读一遍，别猜接口）：`frontend/src/components/board/BoardTable.vue`、`frontend/src/components/board/BoardDetailPanel.vue`、`frontend/src/components/dashboard/TopBoards.vue`、`frontend/src/components/dashboard/MarketIndices.vue`、`frontend/src/components/dashboard/MarketAiSummary.vue`、`frontend/src/components/base/PriceDisplay.vue`、`frontend/src/components/base/MetricCell.vue`、`frontend/src/components/base/StockName.vue`、`frontend/src/components/base/StatusState.vue`、`frontend/src/components/base/SectionPanel.vue`。

- [ ] **Step 2: 实现 UsIndexStrip**

模板结构（script setup；涨跌色与格式复用 base，不写硬编码 hex）：

```vue
<template>
  <div class="us-index-strip" data-testid="us-index-strip">
    <template v-if="summary && summary.indices && summary.indices.length">
      <div class="us-index-strip__quote" v-for="idx in summary.indices" :key="idx.symbol">
        <div class="us-index-strip__name">{{ idx.name }}</div>
        <PriceDisplay
          :price="safeNumber(idx.value)"
          :change="safeNumber(idx.change_amount)"
          :change-percent="safeNumber(idx.change_pct)"
          size="md"
        />
      </div>
      <div class="us-index-strip__breadth">
        <MetricCell label="成分上涨" :value="summary.advancers" tone="positive" />
        <MetricCell label="成分下跌" :value="summary.decliners" tone="negative" />
      </div>
    </template>
    <StatusState v-else-if="loading" state="loading" :min-height="72" />
    <StatusState v-else state="empty" title="暂无美股数据" :min-height="72" />
  </div>
</template>
```

（loading/error 由父级 `useAsyncSection` 状态驱动——UsIndexStrip 只消费 summary/loading。执行者按 MarketIndices.vue 的写法补齐 error 分支。`PriceDisplay/MetricCell/StatusState` 均 `import` base 组件，样式类走本组件 scoped + token。）

- [ ] **Step 3: 实现 UsSectorTable（11 行全量榜）**

仿 BoardTable 行按钮范式；**必须无 `el-pagination`、无搜索 `el-input`、无排序下拉**。每行左侧「中文板块名 + 英文小字 / 领涨 ticker·涨跌幅 / 涨 n 跌 m」，右列 `PercentageDisplay :value="row.change_pct"`。副标题固定文案「标普500成分等权聚合 · 非官方板块指数」（Global Constraint 2）。行按钮高亮 `selectedName`。

```vue
<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="us-sector-table__head">
        <span class="us-sector-table__title">GICS 行业板块</span>
        <span class="us-sector-table__note">标普500成分等权聚合 · 非官方板块指数</span>
      </div>
    </template>
    <StatusState v-if="error" state="error" title="板块加载失败" @retry="$emit('retry')" />
    <StatusState v-else-if="loading" state="loading" :min-height="220" />
    <template v-else-if="sectors.length">
      <div class="us-sector-list" role="list">
        <button
          v-for="s in sectors"
          :key="s.name"
          type="button"
          class="us-sector-row"
          :class="{ 'us-sector-row--active': s.name === selectedName }"
          role="listitem"
          @click="$emit('select', s)"
        >
          <span class="us-sector-row__main">
            <span class="us-sector-row__name">
              {{ s.name }}
              <i class="us-sector-row__en">{{ s.name_en }}</i>
            </span>
            <span class="us-sector-row__meta">
              领涨 {{ s.leading_symbol }} {{ formatChangePct(s.leading_change_pct) }}
              · 涨 {{ s.advancers }} / 跌 {{ s.decliners }}
            </span>
          </span>
          <PercentageDisplay :value="s.change_pct" size="md" />
        </button>
      </div>
    </template>
    <StatusState v-else state="empty" title="暂无板块数据" />
  </SectionPanel>
</template>
```

（`SectionPanel/StatusState/PercentageDisplay` import 自 base；`formatChangePct` 从 `@/utils/format` 引入。空态分支的 loading 覆盖由父级 state 传入。写前对照 BoardTable 的 loading/error/empty 三分支措辞与 `StatusState` 用法补全。）

- [ ] **Step 4: 实现 UsSectorDetailPanel（容器切换）**

容器切换核心（其余行内容仿 BoardDetailPanel 但字段换成 UsSector/UsConstituent）：

```js
import { computed } from 'vue'
import { ElDrawer } from 'element-plus'
import SectionPanel from '../base/SectionPanel.vue'

const detailContainer = computed(() => (props.mobile ? ElDrawer : SectionPanel))
```

模板给两容器共用的「内容块」：顶部板块事实（`board.name` + `PercentageDisplay`，领涨 ticker、涨/跌家数、成分数）；成分股列表（`stocks`，行 = `StockName(:name="s.name" :code="s.symbol")` + `PercentageDisplay(:value="s.change_pct")`）。成分行 `@click="$emit('open-symbol', s.symbol)"`（本期点击不跳转，页面层决定是否提示二期）。移动容器属性：`direction="btt"` `size="100%"` `:model-value="visible"`。

- [ ] **Step 5: 实现 UsSnapshotCard（Dashboard 卡）**

props/emits 见 Interfaces。模板：`SectionPanel variant="flush"` → header slot 左「美股收盘」+ 右「进入美股复盘 →」link（emit `open`）；body：3 指数联排（复用第 2 步的指数行样式，可抽小组件内联）→「领涨 / 领跌板块」芯片行（每芯片 emit `sector`，点 chip 深链 `?sector=`）→ 底部口径小字「按标普500成分统计 · 美东 {summary.as_of} 收盘」。loading/error 用 `StatusState`。整体**只做展示**，数据由父级（Task F5 Dashboard 集成）喂入。

- [ ] **Step 6: MarketAiSummary label prop 化**

读 `MarketAiSummary.vue`，把写死的「AI 盘面结论」改为 `<span>{{ label }}</span>` 并把 `label` 加进 `defineProps`：

```js
defineProps({
  text: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  label: { type: String, default: 'AI 盘面结论' }, // 向后兼容默认
})
```

- [ ] **Step 7: 手动冒烟（可选，起后端 mock 前可先 `vite dev` 看静态编译）**

Run: `cd frontend && npm run dev`（有后端数据时本任务组件尚未接线，仅确认无编译错误即可，随后 Ctrl+C。）

- [ ] **Step 8: 提交**

```bash
git add frontend/src/components/us/ frontend/src/components/dashboard/UsSnapshotCard.vue frontend/src/components/dashboard/MarketAiSummary.vue
git commit -m "feat(us): 美股展示组件与 MarketAiSummary label 化"
```

---

## Task F4: UsMarket 页面装配（深链 + 摘要带）

**Files:**
- Create: `frontend/src/views/UsMarket.vue`
- Create: `frontend/src/components/us/UsAiBand.vue`（AI 一句话通栏，包一层 `MarketAiSummary`，`label="今日主线"`）
- Test: `frontend/tests/us-market-contract.test.js`（追加页面断言）

**Interfaces:**
- Consumes: `useUsMarket()`、`getUsSectorStocks`、base 组件、Task F3 组件。
- Produces: `UsMarket.vue`（路由 `/us`）。路由 query：`?sector=<中文板块名>`，进入/刷新还原选中并请求成分；关闭详情 replace 回 `/us`。

**页面结构（方向一 = A 骨架 + B 顶部叙事摘要带；无分页/搜索）：**
`workbench-page` → header（h1「美股复盘」+ `as_of` 角标 + 刷新按钮）→ ① 全宽摘要带（`UsIndexStrip` 3 指数）→ ② AI 一句话通栏 `UsAiBand`（label「今日主线」，刷新按钮）→ ③ `.workbench-grid--primary`：左 `UsSectorTable`（11 行全量）、右 `UsSectorDetailPanel`。

- [ ] **Step 1: 追加页面契约断言**

在 `frontend/tests/us-market-contract.test.js` 追加：

```js
test('UsMarket 页面骨架 = workbench-page + 摘要带 + 主从 grid', async () => {
  const code = await read('views/UsMarket.vue')
  assert.match(code, /class="us-market-page workbench-page/)
  assert.match(code, /UsIndexStrip/)
  assert.match(code, /UsAiBand|MarketAiSummary/)
  assert.match(code, /UsSectorTable/)
  assert.match(code, /UsSectorDetailPanel/)
  assert.match(code, /data-page-title/)
})

test('UsMarket 页面不出现分页/搜索控件', async () => {
  const code = await read('views/UsMarket.vue')
  assert.doesNotMatch(code, /el-pagination/)
  assert.doesNotMatch(code, /el-input/)
  assert.doesNotMatch(code, /el-select/)
})

test('UsMarket 支持 ?sector= 深链还原', async () => {
  const code = await read('views/UsMarket.vue')
  assert.match(code, /route\.query\.sector|query\.sector/)
  assert.match(code, /getUsSectorStocks/)
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && node --test tests/us-market-contract.test.js`
Expected: FAIL。

- [ ] **Step 3: 读参照并实现页面**

先 `Read frontend/src/views/BoardMonitor.vue` 与 `frontend/src/components/board/BoardDetailPanel.vue`（query 同步 + 桌面/移动容器切换的现成范式）。实现 `UsMarket.vue`，要点：

- `useResponsive()` → `isMobile`；`const { summarySection, sectorsSection, aiText, aiLoading, aiError, generateAiSummary, closeAiSource } = useUsMarket()`。
- 选中态：`const selected = ref(null)`（UsSector）；成分列表用 `useAsyncSection(() => getUsSectorStocks(selected.value.name), { initialData: [] })`（闭包带参 fetcher，仅在 `selectSector` 时 `stocksSection.run()`；若 `useAsyncSection` 已内置 requestId 防串号则无需额外闸门，切换板块快速点击时以其实装为准，不自己另造并发闸）。
- query 同步：`onMounted` 读 `route.query.sector` → 找到对应板块行则 `selectSector`；`watch(() => route.query.sector)` 还原；`selectSector(s)` 先 `router.replace({ query: { ...route.query, sector: s.name } })` 再拉成分；`closeSector()` `router.replace('/us')` 并清 `selected`。
- 进入即 `summarySection.run()` + `sectorsSection.run()` + `generateAiSummary()`；手动刷新按钮重跑三者。**不加 30s 轮询**（收盘复盘数据当日不变）。
- `onUnmounted(() => closeAiSource())`。
- 成分行点击：本任务阶段 `open-symbol` emit 只 `console.info('二期开放美股个股详情', symbol)` 或 `ElMessage.info('个股详情二期开放')`——不跳转（Global Constraint 7）。
- 页面根类 `us-market-page workbench-page`；页面头用 `workbench-page__header`；`as_of` 角标文本「美东 {{ summaryData.as_of }} 收盘」放 header 副位（`summaryData = summarySection.data`）。

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && node --test tests/us-market-contract.test.js`
Expected: 全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/UsMarket.vue frontend/src/components/us/UsAiBand.vue frontend/tests/us-market-contract.test.js
git commit -m "feat(us): 美股复盘页面装配（摘要带 + 全量板块榜 + ?sector= 深链）"
```

---

## Task F5: 导航/路由/图标接入 + Dashboard 卡片

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/Layout.vue`
- Modify: `frontend/src/components/app/DesktopSidebar.vue`
- Modify: `frontend/src/components/app/MobileNav.vue`
- Modify: `frontend/src/plugins/elementPlus.js`
- Modify: `frontend/src/views/Dashboard.vue`
- Create: `frontend/tests/us-navigation-contract.test.js`

**Interfaces:**
- `/us` 路由 name `UsMarket`、`meta: { title: '美股复盘', icon: 'Globe' }`；导航文案 title「美股」、compactTitle「美股」，位于「板块监控」与「机会雷达」之间。图标用 Element Plus `Globe`，注册进 `plugins/elementPlus.js` `icons` 白名单。

- [ ] **Step 1: 写失败导航契约测试**

`frontend/tests/us-navigation-contract.test.js`：

```js
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { readFile } = require('node:fs/promises')
const { resolve } = require('node:path')

const SRC = resolve(__dirname, '../src')
const read = (p) => readFile(resolve(SRC, p), 'utf8')

test('router 注册 /us 美股复盘路由', async () => {
  const code = await read('router/index.js')
  assert.match(code, /path: '\/us'/)
  assert.match(code, /UsMarket|views\/UsMarket\.vue/)
  assert.match(code, /title: '美股复盘'/)
})

test('Layout navBlueprint 含美股且 icon=Globe', async () => {
  const code = await read('components/Layout.vue')
  assert.match(code, /path: '\/us'/)
  assert.match(code, /title: '美股'/)
  assert.match(code, /icon: 'Globe'/)
})

test('Globe 图标注册进 elementPlus 白名单', async () => {
  const code = await read('plugins/elementPlus.js')
  assert.match(code, /Globe/)
})

test('侧栏与移动导航支持 /us 前缀高亮', async () => {
  const [desk, mob] = await Promise.all([
    read('components/app/DesktopSidebar.vue'),
    read('components/app/MobileNav.vue'),
  ])
  assert.match(desk, /us/)
  assert.match(mob, /us/)
})

test('Dashboard 接入 UsSnapshotCard', async () => {
  const dash = await read('views/Dashboard.vue')
  assert.match(dash, /UsSnapshotCard/)
  assert.match(dash, /useUsCard/)
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && node --test tests/us-navigation-contract.test.js`
Expected: FAIL。

- [ ] **Step 3: 接入导航与路由**

1. `router/index.js`：在 `/board` 与机会雷达路由之间插入（懒加载与相邻路由同款）：

```js
{
  path: '/us',
  name: 'UsMarket',
  component: () => import('../views/UsMarket.vue'),
  meta: { title: '美股复盘', icon: 'Globe' },
},
// 二期：美股个股详情占位（本期不实现）
// { path: '/us/stock/:symbol', name: 'UsStockDetail', component: () => import('../views/UsStockDetail.vue'), meta: { hidden: true } },
```

2. `components/Layout.vue`：在 `navBlueprint` 中「板块监控」与「机会雷达」之间追加：

```js
{ path: '/us', title: '美股', icon: 'Globe' },
```

3. `components/app/DesktopSidebar.vue` 与 `components/app/MobileNav.vue`：各自 `isActive` 增加对 id 为 `us` 的前缀匹配（与 `stock`/`reports` 分支同款写法）：

```js
if (item.id === 'us') return route.path === '/us' || route.path.startsWith('/us/')
```

4. `plugins/elementPlus.js`：`icons` 对象加入 `Globe: Globe`，并把 `Globe` 加进 import 语句。

- [ ] **Step 4: Dashboard 插入卡片 + useUsCard 接线**

`Dashboard.vue` 在 `<MarketAiSummary ... />` 之后追加（占位变量取自 `useUsCard()`）：

```vue
<UsSnapshotCard
  class="dashboard-page__us-card"
  :summary="cardData"
  :loading="cardLoading"
  :error="cardError"
  @retry="retryCard"
  @open="router.push('/us')"
  @sector="(name) => router.push({ path: '/us', query: { sector: name } })"
/>
```

并在 script 内 `const { cardData, cardLoading, cardError, retryCard } = useUsCard()`、`onMounted(retryCard)`（或并入现有 `onMounted`）。Dashboard 样式：卡片放 AI 通栏**之下**，全宽 `SectionPanel`，移动端折叠为 3 指数行 + 领涨/领跌首行。

- [ ] **Step 5: 运行确认通过**

Run: `cd frontend && node --test tests/us-navigation-contract.test.js tests/us-market-contract.test.js tests/navigation-regression.test.js tests/new-feature-style-contract.test.js`
Expected: 全部 PASS（含既有回归——若 `navigation-regression.test.js` 对导航图标数有下限断言，新增图标只增不减，应通过）。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/router/index.js frontend/src/components/Layout.vue frontend/src/components/app/DesktopSidebar.vue frontend/src/components/app/MobileNav.vue frontend/src/plugins/elementPlus.js frontend/src/views/Dashboard.vue frontend/tests/us-navigation-contract.test.js
git commit -m "feat(us): /us 路由与导航 + Dashboard 美股收盘卡片"
```

---

## Task F6: 端到端收尾（后端接线冒烟 + 全量回归 + README）

**Files:**
- Modify: `README.md`（功能清单 + API 表）
- Run: 后端全量测试、前端全量契约测试、前端生产构建

- [ ] **Step 1: 更新 README**

功能清单加「美股复盘（`/us`）：3 大美股指数、11 个 GICS 板块（标普500成分等权口径）、板块内领涨领跌成分、AI 一句话主线（SSE）」，API 表加 `GET /api/us/summary|sectors|sectors/{name}/constituents|ai-summary`，并注明数据口径与「非官方板块指数、按标普500成分统计、二期含 A 股联动与个股详情」。

- [ ] **Step 2: 后端全量测试**

Run: `cd backend && source venv/bin/activate && python -m pytest -q`
Expected: 全绿（含既有 A 股与 auth/report/monitor 用例）。

- [ ] **Step 3: 前端全量契约测试**

Run: `cd frontend && node --test tests/*.test.js`
Expected: 全绿。

- [ ] **Step 4: 生产构建**

Run: `cd frontend && npm run build`
Expected: 构建成功、无未使用 import 报错。

- [ ] **Step 5: 真实数据冒烟（可选但推荐）**

启动后端：`cd backend && source venv/bin/activate && uvicorn app.main:app --port 52764`；另开终端 `cd frontend && npm run dev`。
手动核对：`/us` 显示 3 指数与 11 板块（可能有部分成分拉取失败致某板块成员缺失，属预期降级）；点板块右栏/抽屉出成分；`/` Dashboard 底部出现「美股收盘」卡；板块卡/榜副标题口径文案出现；刷新 `/us?sector=信息技术` 深链还原。美股盘后/周末无当日 bar 时，页面 `as_of` 停在上一个交易日——符合预期。

- [ ] **Step 6: 提交**

```bash
git add README.md
git commit -m "docs(us): README 补美股复盘功能与 API 表"
```

---

## Self-Review（对照 spec 的自查结论）

**Spec 覆盖核对：**
- 3 指数收盘（01 §2.1 / 02 §8.1）→ Task 3（fetch）+ Task 7（summary）+ UsIndexStrip ✓
- 11 GICS 板块等权聚合（01 方案 B / 02 §8.2）→ Task 1（股池）+ Task 5（聚合）+ Task 7 + UsSectorTable ✓
- 板块成分领涨领跌（01 / 02 §8.3）→ Task 5 `sector_constituents` + UsSectorDetailPanel ✓
- AI 一句话（02 §8.4，只陈述不归因 + 兜底）→ Task 8 + UsAiBand ✓
- Dashboard 卡片（02 §6）→ F3 UsSnapshotCard + F5 Dashboard ✓
- 深链 `?sector=`（02 §3.2）→ F4 ✓
- 缓存按 ET 交易日每日一次（01 §5.2）→ Task 6 ✓
- 评审共识必改项 → Global Constraint 1-7 逐条映射：广度口径(T5/T7 UsSummary.breadth_scope)、板块口径标注(T5 method + F3 副标题)、AI 归因禁令(T8 system prompt)、无分页搜索(F4 断言)、市场标签(F3/F4)、无 market_state(Constraint 6)、ticker 隔离(F4 open-symbol 不跳转)。
- 二期留口：`/us/stock/:symbol` 注释、`market` 参数留口、新闻不做 → 本文无对应任务（有意排除，属二期）✓

**占位符扫描：** 无 TBD/TODO 业务步骤。Task 7 Step 4 的「占位 ai 实现」在 Task 8 显式整体替换为真实实现，属分步落地的中间态而非遗留占位。数据资产由 Task 1 脚本实际生成并入库，非手写占位。前端模板凡注明「补齐 xx 分支」的均已给出确定参照文件与 base 用法，且以 F3 Step 1「先读参照文件」作为硬性步骤。

**类型一致性：** `fetch_constituent_quotes` 返回 `(quotes, as_of)` 在所有消费点一致（Task 4 定义、Task 6 `_full_refresh`、Task 7 routes 不直接用）；`aggregate_sectors(members, quotes)` 签名跨 Task 5/6/7 一致；`get_us_snapshot()` 返回的 dataclass 字段 `indices/sectors/quote_map/as_of/updated_at` 在 Task 6/7/8 一致；composable 导出契约在 F2 定义、F4/F5 消费，契约测试兜底。
