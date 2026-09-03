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
