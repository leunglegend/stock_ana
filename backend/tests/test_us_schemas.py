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
