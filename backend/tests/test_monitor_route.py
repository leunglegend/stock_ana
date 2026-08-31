from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.dependencies import get_current_user, get_db
from app.main import app
from app.schemas.monitor import MonitorOverview
from app.services import monitor_service


client = TestClient(app)


def _fake_db():
    return SimpleNamespace()


def test_monitor_requires_authentication():
    response = client.get("/api/monitor/overview")
    assert response.status_code == 401


def test_monitor_rejects_invalid_days():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_db] = lambda: _fake_db()
    try:
        response = client.get("/api/monitor/overview?days=45")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_monitor_returns_404_for_missing_group(monkeypatch):
    async def override_db():
        yield _fake_db()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(
        monitor_service,
        "build_monitor_overview",
        lambda *args, **kwargs: (_ for _ in ()).throw(monitor_service.MonitorGroupNotFound("分组不存在")),
    )
    try:
        response = client.get("/api/monitor/overview?group_id=99")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_monitor_success_response_has_stable_top_level_contract(monkeypatch):
    async def override_db():
        yield _fake_db()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(monitor_service, "build_monitor_overview", lambda *args, **kwargs: MonitorOverview())
    try:
        response = client.get("/api/monitor/overview?group_id=all&days=90")
        assert response.status_code == 200
        assert set(response.json()) >= {"as_of", "market", "summary", "items", "action_queue", "errors"}
    finally:
        app.dependency_overrides.clear()


def test_monitor_passes_optional_code_for_single_stock_retry(monkeypatch):
    async def override_db():
        yield _fake_db()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_db] = override_db
    calls = []

    def fake_overview(*args, **kwargs):
        calls.append(kwargs)
        return MonitorOverview()

    monkeypatch.setattr(monitor_service, "build_monitor_overview", fake_overview)
    try:
        response = client.get("/api/monitor/overview?group_id=all&days=90&code=600519")
        assert response.status_code == 200
        assert calls[0]["code"] == "600519"
    finally:
        app.dependency_overrides.clear()
