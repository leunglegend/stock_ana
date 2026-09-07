import unittest
from unittest.mock import patch

from app.services import us_cache
from app.services.us_cache import _decide_refresh, get_us_snapshot, reset_cache
from app.models.schemas import UsConstituent, UsIndexQuote


class DecideRefreshTest(unittest.TestCase):
    """纯决策函数：force / as_of 变化 / TTL 组合下的动作选择。"""

    def test_first_ever_call_is_sync_full(self):
        cache = {"as_of": None, "time": 0.0, "indices": [], "sectors": []}
        self.assertEqual(_decide_refresh(cache, as_of="2026-09-02", now=100.0,
                                         force=False, probe_ttl=300.0), "sync_full")

    def test_cache_fresh_hit_without_probe(self):
        cache = {"as_of": "2026-09-02", "time": 50.0, "sectors": ["x"]}
        # now=100，距上次 50s < probe 触发下限；直接命中
        self.assertEqual(_decide_refresh(cache, as_of=None, now=100.0,
                                         force=False, probe_ttl=300.0), "hit")

    def test_after_probe_ttl_probes(self):
        cache = {"as_of": "2026-09-02", "time": 10.0, "sectors": ["x"]}
        # now=400，距上次 390s >= 探测间隔；需要 probe
        self.assertEqual(_decide_refresh(cache, as_of=None, now=400.0,
                                         force=False, probe_ttl=300.0), "probe")

    def test_asof_changed_triggers_full(self):
        cache = {"as_of": "2026-09-02", "time": 10.0, "sectors": ["x"]}
        self.assertEqual(_decide_refresh(cache, as_of="2026-09-03", now=400.0,
                                         force=False, probe_ttl=300.0), "sync_full")

    def test_force_always_full(self):
        cache = {"as_of": "2026-09-03", "time": 999.0, "sectors": ["x"]}
        self.assertEqual(_decide_refresh(cache, as_of="2026-09-03", now=1000.0,
                                         force=True, probe_ttl=300.0), "sync_full")


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        reset_cache()

    def test_first_call_builds_snapshot(self):
        members = _fake_members()
        with patch.object(us_cache, "_get_ak", return_value=object()), \
                patch.object(us_cache.us_data, "fetch_index_asof", return_value="2026-09-02"), \
                patch.object(us_cache.us_data, "fetch_index_quotes", side_effect=_fake_indices), \
                patch.object(us_cache.us_data, "fetch_constituent_quotes", side_effect=_fake_constituents), \
                patch.object(us_cache.us_universe, "load_us_constituents", return_value=members):
            snap = get_us_snapshot()
        self.assertEqual(snap.as_of, "2026-09-02")
        self.assertEqual(len(snap.quote_map), 3)
        self.assertEqual([s.name for s in snap.sectors],
                         ["信息技术", "能源"])  # +1.0 vs -1.5 降序
        self.assertEqual([i.symbol for i in snap.indices], ["DJI", "SPX", "IXIC"])

    def test_refresh_failure_returns_stale_and_second_hit_reuses(self):
        members = _fake_members()
        calls = {"n": 0}

        def flaky_constituents(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                return _fake_constituents(None)
            raise RuntimeError("network down")

        with patch.object(us_cache, "_get_ak", return_value=object()), \
                patch.object(us_cache.us_data, "fetch_index_asof", return_value="2026-09-02"), \
                patch.object(us_cache.us_data, "fetch_index_quotes", side_effect=_fake_indices), \
                patch.object(us_cache.us_data, "fetch_constituent_quotes", side_effect=flaky_constituents), \
                patch.object(us_cache.us_universe, "load_us_constituents", return_value=members), \
                patch.object(us_cache.time, "time", return_value=100.0):
            snap1 = get_us_snapshot()            # 首次成功
            snap2 = get_us_snapshot()            # 命中缓存，不触发重拉
        self.assertEqual(snap1.as_of, "2026-09-02")
        self.assertEqual(calls["n"], 1)
        self.assertIs(snap2, snap1)


def _fake_members():
    from app.services.us_universe import UsUniverseMember
    return [
        UsUniverseMember("AAPL", "Apple", "Information Technology"),
        UsUniverseMember("MSFT", "Microsoft", "Information Technology"),
        UsUniverseMember("XOM", "Exxon", "Energy"),
    ]


def _fake_indices(*a, **k):
    return [UsIndexQuote(symbol="DJI", name="道琼斯", value=1, change_pct=0),
            UsIndexQuote(symbol="SPX", name="标普500", value=1, change_pct=0),
            UsIndexQuote(symbol="IXIC", name="纳斯达克", value=1, change_pct=0)]


def _fake_constituents(members, **k):
    specs = {"AAPL": 1.0, "MSFT": 2.0, "XOM": -1.5}
    quotes = [UsConstituent(symbol=s, name=s, price=100 + p, change_amount=p, change_pct=p)
              for s, p in specs.items()]
    return quotes, "2026-09-02"


if __name__ == "__main__":
    unittest.main()
