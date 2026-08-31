from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.models.schemas import KLineItem, MarketSummary
from app.schemas.monitor import MonitorQuote, MonitorSnapshot
from app.services import monitor_service


def _snapshot(code, change_pct=1.0):
    rows = [
        KLineItem(date="2026-08-29", open=9, close=9.5, high=9.8, low=8.8, volume=100,
                  ma5=9.2, ma20=9.0, dif=0.2, dea=0.1, rsi6=55),
        KLineItem(date="2026-08-30", open=9.5, close=10, high=10.2, low=9.4, volume=120,
                  ma5=9.6, ma20=9.1, dif=0.3, dea=0.1, rsi6=60),
    ]
    return MonitorSnapshot(
        code=code,
        name=code,
        rows=rows,
        kline=rows,
        quote=MonitorQuote(
            price=10,
            change_pct=change_pct,
            change_amount=0.1,
            volume=120,
            source="kline",
            as_of="2026-08-30",
        ),
        sparkline=[{"date": row.date, "close": row.close} for row in rows],
    )


def _db_with_items(*items):
    groups = {}
    for item in items:
        groups.setdefault(item.group_id, SimpleNamespace(id=item.group_id, name=item.group_name, stocks=[]))
        groups[item.group_id].stocks.append(item)
    return SimpleNamespace(groups=list(groups.values()))


def test_deduplicates_codes_across_groups_and_returns_summary(monkeypatch):
    items = [
        SimpleNamespace(id=1, group_id=10, group_name="重点", stock_code="600519", stock_name="贵州茅台", cost=8, remark=""),
        SimpleNamespace(id=2, group_id=11, group_name="观察", stock_code="600519", stock_name="贵州茅台", cost=9, remark=""),
        SimpleNamespace(id=3, group_id=10, group_name="重点", stock_code="000001", stock_name="平安银行", cost=0, remark=""),
    ]
    calls = []

    def loader(code, days):
        calls.append((code, days))
        return _snapshot(code)

    monkeypatch.setattr(monitor_service.watchlist_service, "get_groups_with_stocks", lambda db, user_id: db.groups)
    monitor_service.clear_monitor_cache()

    result = monitor_service.build_monitor_overview(
        _db_with_items(*items), user_id=7, days=90,
        snapshot_loader=loader,
        market_loader=lambda: MarketSummary(sh_change_pct=0.2, rise_count=60, fall_count=30, flat_count=10),
    )

    assert calls == [("600519", 90), ("000001", 90)]
    assert result.summary.stock_count == 3
    assert len(result.items) == 3
    assert result.items[0].code == "600519"


def test_uses_cached_snapshot_when_loader_fails(monkeypatch):
    item = SimpleNamespace(id=1, group_id=10, group_name="重点", stock_code="600519", stock_name="贵州茅台", cost=0, remark="")
    monkeypatch.setattr(monitor_service.watchlist_service, "get_groups_with_stocks", lambda db, user_id: db.groups)
    monitor_service.clear_monitor_cache()
    monitor_service._snapshot_cache[("600519", 90)] = monitor_service.CacheEntry(
        value=_snapshot("600519"),
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    def loader(_code, _days):
        raise RuntimeError("network down")

    result = monitor_service.build_monitor_overview(
        _db_with_items(item), user_id=7, days=90,
        snapshot_loader=loader,
        market_loader=lambda: None,
    )

    assert result.items[0].quote.stale is True
    assert result.items[0].quote.source == "cache"
    assert result.items[0].errors == ["network down"]
    assert result.items[0].status == "attention"
    assert result.action_queue[0].code == "600519"


def test_fresh_cache_hit_is_explicitly_marked_as_cache(monkeypatch):
    monitor_service.clear_monitor_cache()
    first = _snapshot("600519")
    calls = []

    def loader(code, days):
        calls.append((code, days))
        return first

    now = datetime.now(timezone.utc)
    monitor_service._snapshot_cache[("600519", 90)] = monitor_service.CacheEntry(
        value=first,
        expires_at=now + timedelta(seconds=30),
    )

    snapshot = monitor_service._load_one_snapshot("600519", 90, loader, now)

    assert calls == []
    assert snapshot.quote.source == "cache"
    assert snapshot.quote.stale is True


def test_empty_watchlist_returns_stable_empty_overview(monkeypatch):
    monkeypatch.setattr(monitor_service.watchlist_service, "get_groups_with_stocks", lambda db, user_id: [])
    result = monitor_service.build_monitor_overview(
        SimpleNamespace(), user_id=7, snapshot_loader=lambda *_: _snapshot("x"), market_loader=lambda: None
    )
    assert result.items == []
    assert result.action_queue == []
    assert result.summary.stock_count == 0


def test_missing_market_summary_is_marked_stale_and_reported(monkeypatch):
    monkeypatch.setattr(monitor_service.watchlist_service, "get_groups_with_stocks", lambda db, user_id: [])

    result = monitor_service.build_monitor_overview(
        SimpleNamespace(), user_id=7, market_loader=lambda: None
    )

    assert result.market.environment == "未知"
    assert result.market.stale is True
    assert result.errors[0].scope == "market"


def test_code_filter_only_loads_requested_stock_and_uses_source_time(monkeypatch):
    items = [
        SimpleNamespace(id=1, group_id=10, group_name="重点", stock_code="600519", stock_name="贵州茅台", cost=0, remark=""),
        SimpleNamespace(id=2, group_id=10, group_name="重点", stock_code="000001", stock_name="平安银行", cost=0, remark=""),
    ]
    calls = []
    snapshot_time = datetime(2026, 8, 30, 8, 30, tzinfo=timezone.utc)
    market_time = datetime(2026, 8, 30, 8, 35, tzinfo=timezone.utc)

    def loader(code, days):
        calls.append((code, days))
        return _snapshot(code).model_copy(update={"fetched_at": snapshot_time})

    monkeypatch.setattr(monitor_service.watchlist_service, "get_groups_with_stocks", lambda db, user_id: db.groups)
    monitor_service.clear_monitor_cache()
    result = monitor_service.build_monitor_overview(
        _db_with_items(*items), user_id=7, days=90, code="000001",
        snapshot_loader=loader,
        market_loader=lambda: (MarketSummary(sh_change_pct=0.2), False, market_time),
        now=datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc),
    )

    assert calls == [("000001", 90)]
    assert [item.code for item in result.items] == ["000001"]
    assert result.market.as_of == market_time
    assert result.as_of == snapshot_time
