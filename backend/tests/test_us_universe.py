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
