"""个股 AI 流式分析路由契约测试。

前端 EventSource 依赖 GET /api/stock/{code}/analyze 返回 SSE；
该路由曾因重构丢失 @router.get 装饰器而整体 404。
"""

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def _noop_stock_info(_code):
    return SimpleNamespace(code="600519", name="贵州茅台")


def _noop_kline(_code, _period, _days):
    return SimpleNamespace(code="600519", name="贵州茅台", kline=[1])


def _noop_financial(_code):
    return SimpleNamespace()


async def _fake_ai_stream(_info, _kline, _financial):
    yield "第一段分析"
    yield "第二段分析"


def test_stock_analyze_route_returns_sse_stream():
    """GET /api/stock/{code}/analyze 必须存在并按 SSE 流式返回内容。"""
    with patch("app.routes.stock.stock_data.get_stock_info", side_effect=_noop_stock_info), \
            patch("app.routes.stock.stock_data.get_kline_data", side_effect=_noop_kline), \
            patch("app.routes.stock.stock_data.get_financial_data", side_effect=_noop_financial), \
            patch("app.routes.stock.analyze_stock_stream", side_effect=_fake_ai_stream):
        with TestClient(app) as client:
            response = client.get("/api/stock/600519/analyze")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert "第一段分析" in response.text
    assert "[DONE]" in response.text
