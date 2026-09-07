from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.dependencies import get_current_user, get_db
from app.main import app
from app.routes import report as report_route
from app.services import report_service


client = TestClient(app)


def _override_deps(db):
    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_db] = override_db


def test_generate_without_watchlist_returns_400_and_creates_no_report(monkeypatch):
    _override_deps(SimpleNamespace())
    monkeypatch.setattr(
        report_service.watchlist_service,
        "get_user_watchlist_stocks",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(report_service, "get_report_by_date", lambda *args, **kwargs: None)
    created = []
    monkeypatch.setattr(
        report_service,
        "create_pending_report",
        lambda *args, **kwargs: created.append(1) or SimpleNamespace(id=999),
    )
    try:
        response = client.post("/api/reports/generate")

        assert response.status_code == 400
        assert "自选股" in response.json()["detail"]
        assert created == []
    finally:
        app.dependency_overrides.clear()


def test_generate_without_watchlist_still_leaves_existing_pending_unstuck(monkeypatch):
    """服务侧兜底：任务启动时自选股已为空，不能留下永久 pending。"""
    db = SimpleNamespace()
    monkeypatch.setattr(
        report_service.watchlist_service,
        "get_user_watchlist_stocks",
        lambda *args, **kwargs: [],
    )
    existing = SimpleNamespace(id=42, status="pending", error_msg="")
    monkeypatch.setattr(report_service, "get_report_by_date", lambda *args, **kwargs: existing)
    updates = []

    def fake_update_status(_db, report_id, status, error_msg=""):
        updates.append((report_id, status, error_msg))

    monkeypatch.setattr(report_service, "update_report_status", fake_update_status)

    result = report_service.generate_daily_report_for_user(db, 7, date.today())

    assert result is None
    assert updates == [(42, "failed", "暂无自选股，无法生成复盘报告")]


def test_generate_with_watchlist_keeps_existing_pending_flow(monkeypatch):
    """有自选股时仍按原契约返回 200 并创建 pending 记录。"""
    _override_deps(SimpleNamespace())
    monkeypatch.setattr(
        report_service.watchlist_service,
        "get_user_watchlist_stocks",
        lambda *args, **kwargs: [("600519", "贵州茅台")],
    )
    monkeypatch.setattr(report_service, "get_report_by_date", lambda *args, **kwargs: None)
    created = []

    def fake_create_pending(_db, user_id, report_date):
        created.append((user_id, report_date))
        return SimpleNamespace(id=888)

    monkeypatch.setattr(report_service, "create_pending_report", fake_create_pending)
    monkeypatch.setattr(report_route, "_run_generate_task", lambda *args, **kwargs: None)
    try:
        response = client.post("/api/reports/generate")

        assert response.status_code == 200
        assert response.json()["report_id"] == 888
        assert len(created) == 1
    finally:
        app.dependency_overrides.clear()


def test_generate_existing_completed_takes_priority_over_empty_watchlist(monkeypatch):
    """已有可用报告时不因当前无自选股而报错，仍返回“今日报告已存在”。"""
    _override_deps(SimpleNamespace())
    existing = SimpleNamespace(id=1)
    monkeypatch.setattr(report_service, "get_report_by_date", lambda *args, **kwargs: existing)
    monkeypatch.setattr(report_service, "is_report_usable", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        report_service.watchlist_service,
        "get_user_watchlist_stocks",
        lambda *args, **kwargs: [],
    )

    def unexpected_create(*args, **kwargs):
        raise AssertionError("不应为已有报告创建新记录")

    monkeypatch.setattr(report_service, "create_pending_report", unexpected_create)
    try:
        response = client.post("/api/reports/generate")

        assert response.status_code == 200
        assert response.json()["message"] == "今日报告已存在"
    finally:
        app.dependency_overrides.clear()
