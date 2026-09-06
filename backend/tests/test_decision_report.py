import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import FinancialData, KLineData, KLineItem, StockInfo
from app.services import ai_analyst
from app.services import stock_data


client = TestClient(app)


def _row(index=0, **overrides):
    values = {
        "date": f"2026-08-{index + 1:02d}",
        "open": 10.0,
        "close": 10.0 + index * 0.05,
        "high": 10.2 + index * 0.05,
        "low": 9.8 + index * 0.05,
        "volume": 100.0,
        "ma5": 10.0,
        "ma10": 9.9,
        "ma20": 9.8,
        "dif": 0.2,
        "dea": 0.1,
        "rsi6": 50.0,
    }
    values.update(overrides)
    return KLineItem(**values)


def _stock():
    return StockInfo(
        code="600519", name="测试股票", price=12, change_pct=1,
        change_amount=0.12, open=11.9, pre_close=11.88,
        high=12.2, low=11.8, volume=1000, amount=12000,
    )


def _kline():
    return KLineData(code="600519", name="测试股票", kline=[_row(0), _row(1)])


class DecisionReportNormalizationTest(unittest.TestCase):
    def test_normalizes_rating_score_and_unavailable_sections(self):
        result = ai_analyst._normalize_decision_report({
            "conclusion": {"label": "卖出", "score": 140, "rationale": "  需要控制风险。 "},
            "risks": [" 风险一 ", "", 123],
        })
        self.assertEqual(result["conclusion"]["action"], "sell")
        self.assertEqual(result["conclusion"]["score"], 100)
        self.assertEqual(result["risks"], ["风险一"])
        self.assertEqual(result["sentiment"]["status"], "unavailable")
        self.assertEqual(result["latest_developments"]["status"], "unavailable")

    def test_invalid_action_falls_back_to_label_and_score_is_bounded(self):
        result = ai_analyst._normalize_decision_report({
            "conclusion": {"action": "maybe", "label": "买入", "score": -2.8},
            "trend": "not an object",
            "levels": None,
        })
        self.assertEqual(result["conclusion"]["action"], "buy")
        self.assertEqual(result["conclusion"]["score"], 0)
        self.assertEqual(result["trend"], {})
        self.assertEqual(result["levels"], {})

    def test_generate_rejects_malformed_json(self):
        response = SimpleNamespace(content=[SimpleNamespace(text="not json")])
        client_stub = SimpleNamespace(messages=SimpleNamespace(create=AsyncMock(return_value=response)))
        with patch.object(ai_analyst.settings, "ARK_API_KEY", "test-key"), \
                patch.object(ai_analyst.settings, "ARK_MODEL", "test-model"), \
                patch.object(ai_analyst, "_get_client", return_value=client_stub):
            with self.assertRaisesRegex(RuntimeError, "决策报告生成失败"):
                asyncio.run(ai_analyst.generate_decision_report(_stock(), _kline(), FinancialData(code="600519", name="测试股票"), []))

    def test_generate_reports_unavailable_ai_without_calling_client(self):
        # ai_available 是只读 property（由 ARK_API_KEY/ARK_MODEL 派生），不能直接 patch；
        # 置空 API Key 让其自然返回 False。
        with patch.object(ai_analyst.settings, "ARK_API_KEY", ""), \
                patch.object(ai_analyst, "_get_client") as get_client:
            with self.assertRaisesRegex(RuntimeError, "未配置 API Key"):
                asyncio.run(ai_analyst.generate_decision_report(_stock(), _kline(), FinancialData(code="600519", name="测试股票"), []))
            get_client.assert_not_called()


class DecisionReportRouteTest(unittest.TestCase):
    def setUp(self):
        self.info = _stock()
        self.kline = _kline()
        self.financial = FinancialData(code="600519", name="测试股票", pe=20)

    def test_unknown_stock_returns_404(self):
        with patch.object(stock_data, "get_stock_info", return_value=None), \
                patch.object(stock_data, "get_kline_data", return_value=None):
            response = client.get("/api/stock/999999/decision-report")
        self.assertEqual(response.status_code, 404)

    def test_missing_kline_returns_502(self):
        with patch.object(stock_data, "get_stock_info", return_value=self.info), \
                patch.object(stock_data, "get_kline_data", return_value=None):
            response = client.get("/api/stock/600519/decision-report")
        self.assertEqual(response.status_code, 502)

    def test_quote_fallback_and_deterministic_signals_are_injected(self):
        fallback_kline = KLineData(code="600519", name="测试股票", kline=[_row(0), _row(1, close=11, ma5=10.5, ma20=10)])
        generated = {
            "conclusion": {"action": "hold", "label": "观望", "score": 50, "rationale": "基于输入数据"},
            "trend": {}, "levels": {}, "risks": [], "catalysts": [],
            "sentiment": {"status": "unavailable", "summary": "当前未接入新闻/情绪数据"},
            "fundamentals": {},
            "latest_developments": {"status": "unavailable", "summary": "当前未接入公告与最新动态数据"},
            "checklist": [], "analysis_markdown": "",
        }
        with patch.object(stock_data, "get_stock_info", return_value=None), \
                patch.object(stock_data, "get_kline_data", return_value=fallback_kline), \
                patch.object(stock_data, "get_financial_data", return_value=self.financial), \
                patch("app.routes.stock.generate_decision_report", new=AsyncMock(return_value=generated)) as generate:
            response = client.get("/api/stock/600519/decision-report")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], "600519")
        self.assertEqual(body["data_quality"]["level"], "usable")
        self.assertTrue(any(signal["code"] == "trend-above-ma20" for signal in body["signals"]))
        self.assertEqual(generate.await_args.args[0].price, 11)

    def test_ai_failure_returns_503(self):
        with patch.object(stock_data, "get_stock_info", return_value=self.info), \
                patch.object(stock_data, "get_kline_data", return_value=self.kline), \
                patch.object(stock_data, "get_financial_data", return_value=self.financial), \
                patch("app.routes.stock.generate_decision_report", new=AsyncMock(side_effect=RuntimeError("provider unavailable"))):
            response = client.get("/api/stock/600519/decision-report")
        self.assertEqual(response.status_code, 503)
        self.assertIn("provider unavailable", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
