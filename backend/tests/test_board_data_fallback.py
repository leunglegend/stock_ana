import unittest
from unittest.mock import patch

import pandas as pd

from app.services import board_data
from app.services.board_data import _fetch_board_stocks_sina, _parse_board_stocks


class FakeAkshare:
    def stock_sector_spot(self, indicator):
        self.indicator = indicator
        return pd.DataFrame([
            {"label": "hangye_ZA01", "板块": "农业"},
            {"label": "hangye_ZA02", "板块": "林业"},
            {"label": "hangye_ZA03", "板块": "农业综合"},
            {"label": "hangye_ZB06", "板块": "煤炭开采和洗选业"},
        ])

    def stock_sector_detail(self, sector):
        rows = {
            "hangye_ZA01": [{
                "code": "600354", "name": "敦煌种业", "trade": 8.21,
                "pricechange": 0.75, "changepercent": 10.054,
                "turnoverratio": 20.60294, "per": 91.732, "mktcap": 433325.50768,
            }],
            "hangye_ZA02": [{
                "code": "000592", "name": "平潭发展", "trade": 7.01,
                "pricechange": 0.2, "changepercent": 2.937,
                "turnoverratio": 19.68786, "per": -117.42, "mktcap": 1354178.0,
            }],
            "hangye_ZA03": [{
                "code": "000998", "name": "隆平高科", "trade": 10.1,
                "pricechange": 0.1, "changepercent": 1.0,
                "turnoverratio": 2.0, "per": 30.0, "mktcap": 1000000.0,
            }],
        }
        return pd.DataFrame(rows[sector])


class BoardDataFallbackTest(unittest.TestCase):
    def setUp(self):
        board_data._board_stocks_cache.clear()

    def test_sina_fallback_combines_composite_industry(self):
        ak = FakeAkshare()

        frame = _fetch_board_stocks_sina(ak, "种植业与林业")

        self.assertEqual("行业", ak.indicator)
        self.assertEqual(["600354", "000592"], frame["code"].tolist())

    def test_sina_fields_are_parsed_into_board_stock_contract(self):
        frame = FakeAkshare().stock_sector_detail("hangye_ZA01")

        stocks = _parse_board_stocks(frame)

        self.assertEqual(1, len(stocks))
        self.assertEqual("600354", stocks[0].code)
        self.assertEqual(8.21, stocks[0].price)
        self.assertEqual(10.054, stocks[0].change_pct)
        self.assertEqual(20.60294, stocks[0].turnover_rate)
        self.assertAlmostEqual(43.332550768, stocks[0].total_mv)

    def test_sina_exact_industry_does_not_merge_partial_name_matches(self):
        frame = _fetch_board_stocks_sina(FakeAkshare(), "农业")

        self.assertEqual(["600354"], frame["code"].tolist())

    def test_industry_prefers_fast_sina_source(self):
        frame = FakeAkshare().stock_sector_detail("hangye_ZA01")

        with patch.object(board_data, "_get_ak", return_value=object()), \
                patch.object(board_data, "_fetch_board_stocks_sina", return_value=frame) as sina, \
                patch.object(board_data, "_fetch_board_industry_cons_em") as eastmoney:
            stocks = board_data.get_board_stocks("种植业与林业", "industry")

        self.assertEqual("600354", stocks[0].code)
        sina.assert_called_once()
        eastmoney.assert_not_called()


if __name__ == "__main__":
    unittest.main()
