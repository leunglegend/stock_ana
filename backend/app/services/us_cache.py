"""美股数据快照缓存 —— 按数据日期(as_of)判定，不是 300s 高频 TTL。

成分行情是一次 500 请求 / ~1 分钟的代价换来的，不能像 A 股板块那样
每 5 分钟重拉。策略：
- 首次访问或探测到新浪已入库"新交易日"(as_of 变化) → 同步全量重拉一次；
- 其余时间内命中缓存，且仅每隔 PROBE_TTL 发 1 个轻量探测请求确认 as_of 未变；
- 全量重拉失败 → 保留旧快照并打印（首次失败才返回 None）。

线程安全前提：UsCacheSnapshot 值对象构建后不再被改写，各调用方共享同一
不可变快照；_cache 内部数据只在构建快照时拷贝一次，绝不对外暴露。
"""
import threading
import time

from app.services import us_data, us_universe
from app.services.stock_data import _get_ak
from app.models.schemas import UsConstituent

PROBE_TTL = 300.0      # 探测间隔（秒）
MIN_AGE = 60.0         # 距上次刷新不足此值直接命中，不发探测

_cache = {
    "as_of": None,      # str | None，最近已入库美东交易日
    "indices": [],      # list[UsIndexQuote]
    "sectors": [],      # list[UsSector]（降序）
    "quote_map": {},    # dict[symbol, UsConstituent]
    "time": 0.0,        # 最近一次全量刷新时刻
    "last_probe": 0.0,  # 最近一次探测时刻
    "loading": False,
}
_lock = threading.Lock()
_snap = None           # 内存化的 UsCacheSnapshot 值对象（每次成功全量刷新重建）


def reset_cache():
    """清空缓存（测试用）。"""
    global _snap
    with _lock:
        for k in ("as_of", "indices", "sectors", "quote_map",
                  "time", "last_probe", "loading"):
            _cache[k] = None if k == "as_of" else ({} if k == "quote_map"
                                                   else ([] if k in ("indices", "sectors")
                                                         else 0.0 if k in ("time", "last_probe")
                                                         else False))
        _snap = None


def _decide_refresh(cache, as_of, now, force, probe_ttl=PROBE_TTL):
    """决策下一步动作：'sync_full'（同步全量重拉）| 'probe'（发轻量探测）| 'hit'（直接命中）。"""
    if force or cache["as_of"] is None:
        return "sync_full"
    age = now - cache["time"]
    if age < MIN_AGE:
        return "hit"
    if as_of is not None and as_of != cache["as_of"]:
        return "sync_full"   # 已探测且确认有新交易日数据
    if now - cache.get("last_probe", 0.0) >= probe_ttl:
        return "probe"
    return "hit"


def _full_refresh() -> None:
    """拉全量：指数 + 全部成分并聚合成 sectors/quote_map。失败抛异常由调用方兜底。"""
    global _snap
    ak = _get_ak()
    members = us_universe.load_us_constituents()
    quotes, as_of = us_data.fetch_constituent_quotes(members, ak=ak)
    if not quotes or not as_of:
        raise RuntimeError("美股成分行情拉取为空")
    indices = us_data.fetch_index_quotes(ak=ak)
    sectors = us_data.aggregate_sectors(members, quotes)
    _cache["indices"] = indices
    _cache["sectors"] = sectors
    _cache["quote_map"] = {q.symbol: q for q in quotes}
    _cache["as_of"] = as_of
    _cache["time"] = time.time()
    # R5：构建并内存化快照值对象 —— 拷贝一次，此后所有读复用同一实例
    _snap = UsCacheSnapshot(
        indices=list(_cache["indices"]),
        sectors=list(_cache["sectors"]),
        quote_map=dict(_cache["quote_map"]),
        as_of=_cache["as_of"],
        updated_at=_cache["time"],
    )
    print(f"[us缓存] 全量刷新完成 {as_of}，成分 {len(quotes)}，板块 {len(sectors)}")


def get_us_snapshot(force: bool = False):
    """返回当前快照（线程安全）。首次/新交易日同步全量；否则命中，必要时后台探测。"""
    now = time.time()
    decision = _decide_refresh(_cache, None, now, force)
    if decision == "sync_full":
        with _lock:
            try:
                _full_refresh()
            except Exception as e:
                print(f"[us缓存] 全量刷新失败: {e}")
                if _cache["as_of"] is None:
                    return None
        return _snapshot()
    if decision == "probe":
        # 探测 as_of（1 个轻请求）。失败静默，保持缓存。
        probe_asof = None
        try:
            probe_asof = us_data.fetch_index_asof()
        except Exception as e:
            print(f"[us缓存] as_of 探测失败: {e}")
        with _lock:
            _cache["last_probe"] = time.time()
            if probe_asof is not None and probe_asof != _cache["as_of"]:
                # 数据日期已更新：站到同步刷新一侧
                try:
                    _full_refresh()
                except Exception as e:
                    print(f"[us缓存] 数据更新后全量刷新失败: {e}")
    return _snapshot()


def _snapshot():
    """返回内存化的快照值对象。

    正常情况下每次成功全量刷新已构建 _snap，这里直接复用同一实例。
    仅当 _snap 意外为 None（如被 reset_cache 清空后缓存仍非空）时，
    退回到从 _cache 拷贝构建一次。
    """
    global _snap
    if _snap is None:
        with _lock:
            if _snap is None:
                _snap = UsCacheSnapshot(
                    indices=list(_cache["indices"]),
                    sectors=list(_cache["sectors"]),
                    quote_map=dict(_cache["quote_map"]),
                    as_of=_cache["as_of"],
                    updated_at=_cache["time"],
                )
    return _snap


class UsCacheSnapshot:
    """线程快照值对象（不可变语义：返回副本）。"""
    __slots__ = ("indices", "sectors", "quote_map", "as_of", "updated_at")

    def __init__(self, indices, sectors, quote_map, as_of, updated_at):
        self.indices = indices
        self.sectors = sectors
        self.quote_map = quote_map
        self.as_of = as_of
        self.updated_at = updated_at


def clear_cache_for_tests():
    reset_cache()
