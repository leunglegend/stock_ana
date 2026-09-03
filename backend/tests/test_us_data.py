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


if __name__ == "__main__":
    unittest.main()
