from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from app.main import app


DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"


class FrontendServingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_serves_built_frontend(self):
        response = self.client.get("/")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.headers["content-type"].startswith("text/html"))
        self.assertIn('<div id="app"></div>', response.text)

    def test_vue_route_falls_back_to_frontend_shell(self):
        response = self.client.get("/reports/example-report")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.headers["content-type"].startswith("text/html"))
        self.assertIn('<div id="app"></div>', response.text)

    def test_hashed_asset_has_immutable_cache_header(self):
        asset = next((DIST_DIR / "assets").glob("index-*.js"))
        response = self.client.get(f"/assets/{asset.name}")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            "public, max-age=31536000, immutable",
            response.headers["cache-control"],
        )

    def test_api_route_is_not_captured_by_frontend_fallback(self):
        response = self.client.get("/api/route-that-does-not-exist")

        self.assertEqual(404, response.status_code)
        self.assertTrue(response.headers["content-type"].startswith("application/json"))


if __name__ == "__main__":
    unittest.main()
