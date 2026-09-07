import unittest

import pandas as pd

from app.services.board_data import _parse_board_em, _parse_board_ths


class BoardTurnoverUnitTest(unittest.TestCase):
    """板块 total_turnover 统一为“亿”口径。"""

    def _em_frame(self, **overrides):
        row = {
            "板块名称": "半导体",
            "涨跌幅": 3.8,
            "涨跌额": 12.3,
            "总市值": 272_077_129_6000.0,
            "换手率": 1.2,
            "上涨家数": 30,
            "下跌家数": 10,
            "领涨股票": "中芯国际",
            "领涨股票-涨跌幅": 10.0,
        }
        row.update(overrides)
        return pd.DataFrame([row])

    def test_em_total_market_cap_yuan_is_normalized_to_yi(self):
        boards = _parse_board_em(self._em_frame())

        self.assertEqual(1, len(boards))
        self.assertAlmostEqual(27207.71296, boards[0].total_turnover, places=4)

    def test_em_amount_column_yuan_is_normalized_to_yi(self):
        boards = _parse_board_em(self._em_frame(总市值=float("nan"), 成交额=10_000_000_000.0))

        self.assertAlmostEqual(100.0, boards[0].total_turnover, places=4)

    def test_ths_summary_turnover_in_yi_is_not_divided_again(self):
        frame = pd.DataFrame([
            {
                "板块": "银行",
                "涨跌幅": 0.8,
                "总成交额": 27207.71296,
                "上涨家数": 20,
                "下跌家数": 8,
                "领涨股": "招商银行",
                "领涨股-涨跌幅": 2.1,
            }
        ])

        boards = _parse_board_ths(frame)

        self.assertAlmostEqual(27207.71296, boards[0].total_turnover, places=4)


if __name__ == "__main__":
    unittest.main()
