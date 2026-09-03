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
