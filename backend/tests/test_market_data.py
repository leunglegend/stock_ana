from datetime import datetime, timezone

from app.models.schemas import MarketSummary
from app.services import market_data


def test_market_summary_meta_marks_partial_fetch_as_degraded(monkeypatch):
    fetched_at = datetime(2026, 8, 30, 8, 40, tzinfo=timezone.utc)
    monkeypatch.setattr(market_data, "_fetch_market_summary", lambda: MarketSummary())
    monkeypatch.setattr(market_data, "_summary_last_degraded", True)
    monkeypatch.setattr(market_data, "_summary_cache", {"data": None, "time": None, "fetched_at": None, "degraded": False})
    _FixedDateTime.current = fetched_at
    monkeypatch.setattr(market_data, "datetime", _FixedDateTime)

    summary, stale, actual_fetched_at = market_data.get_market_summary_with_meta()

    assert summary is not None
    assert stale is True
    assert actual_fetched_at == fetched_at


def test_market_summary_cache_hit_keeps_original_fetch_time(monkeypatch):
    original = datetime(2026, 8, 30, 8, 40, tzinfo=timezone.utc)
    monkeypatch.setattr(market_data, "_summary_cache", {
        "data": MarketSummary(sh_change_pct=1.2),
        "time": 1_000_000_000,
        "fetched_at": original,
        "degraded": False,
    })
    monkeypatch.setattr(market_data.time, "time", lambda: 1_000_000_010)

    summary, stale, actual_fetched_at = market_data.get_market_summary_with_meta()

    assert summary.sh_change_pct == 1.2
    assert stale is True
    assert actual_fetched_at == original


class _FixedDateTime:
    current = None

    @classmethod
    def now(cls, tz=None):
        return cls.current

    @classmethod
    def fromtimestamp(cls, timestamp, tz=None):
        return datetime.fromtimestamp(timestamp, tz=tz)
