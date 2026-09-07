"""回归测试：K线参数校验与并发注册竞态转 400。"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from app.main import app
from app.models.schemas import KLineData, KLineItem
from app.routes import auth as auth_route
from app.schemas.auth import UserRegister


client = TestClient(app)


def _kline():
    return KLineData(
        code="600519",
        name="测试股票",
        kline=[
            KLineItem(
                date="2026-08-01",
                open=10.0,
                close=10.0,
                high=10.2,
                low=9.8,
                volume=100.0,
                ma5=10.0,
                ma10=9.9,
                ma20=9.8,
                dif=0.2,
                dea=0.1,
                rsi6=50.0,
            )
        ],
    )


def test_kline_rejects_invalid_period(monkeypatch):
    monkeypatch.setattr(
        "app.routes.stock.stock_data.get_kline_data",
        lambda *args, **kwargs: _kline(),
    )
    response = client.get("/api/stock/600519/kline", params={"period": "hourly"})
    assert response.status_code == 422


def test_kline_rejects_invalid_days(monkeypatch):
    monkeypatch.setattr(
        "app.routes.stock.stock_data.get_kline_data",
        lambda *args, **kwargs: _kline(),
    )
    for days in ("0", "-5", "2501"):
        response = client.get("/api/stock/600519/kline", params={"days": days})
        assert response.status_code == 422, f"days={days} 应返回 422"


def test_kline_accepts_valid_period_and_days(monkeypatch):
    monkeypatch.setattr(
        "app.routes.stock.stock_data.get_kline_data",
        lambda *args, **kwargs: _kline(),
    )
    response = client.get(
        "/api/stock/600519/kline",
        params={"period": "weekly", "days": 250},
    )
    assert response.status_code == 200


def test_register_converts_integrity_error_to_400(monkeypatch):
    user_data = UserRegister(username="race_user", password="secret1")

    def fake_lookup(db, username):
        return None

    def fake_register(db, data):
        raise IntegrityError("INSERT INTO users", {}, Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(auth_route, "get_user_by_username", fake_lookup)
    monkeypatch.setattr(auth_route, "register_user", fake_register)

    with pytest.raises(HTTPException) as exc_info:
        auth_route.register(user_data=user_data, db=object())

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "用户名已被占用"
