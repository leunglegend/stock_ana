import unittest
import pandas as pd

from app.services import us_data
from app.services.us_data import (
    fetch_constituent_quotes, fetch_index_asof, fetch_index_quotes,
    parse_us_daily,
)


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
        self.assertAlmostEqual(by["AAPL"].change_pct, 230.0 / 228.0 * 100 - 100)  # ~0.877
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


if __name__ == "__main__":
    unittest.main()
