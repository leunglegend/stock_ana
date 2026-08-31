"""盘中监控聚合服务。"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable

from sqlalchemy.orm import Session

from app.schemas.monitor import (
    MonitorError,
    MonitorItem,
    MonitorMarket,
    MonitorMetrics,
    MonitorOverview,
    MonitorSnapshot,
    MonitorSummary,
    SignalItem,
)
from app.services import watchlist_service
from app.services.market_data import get_market_summary_with_meta
from app.services.signal_rules import analyze_signals, build_action_queue, classify_market_environment
from app.services.stock_data import get_monitor_snapshot


MONITOR_CACHE_TTL = timedelta(seconds=60)
MONITOR_MAX_WORKERS = 4


@dataclass
class CacheEntry:
    value: MonitorSnapshot
    expires_at: datetime


class MonitorGroupNotFound(ValueError):
    """请求的分组不属于当前用户。"""


_snapshot_cache: dict[tuple[str, int], CacheEntry] = {}
_cache_lock = Lock()


def clear_monitor_cache() -> None:
    with _cache_lock:
        _snapshot_cache.clear()


def build_monitor_overview(
    db: Session,
    user_id: int,
    group_id: str = "all",
    days: int = 90,
    *,
    snapshot_loader: Callable[[str, int], MonitorSnapshot] | None = None,
    market_loader: Callable[[], object] | None = None,
    now: datetime | None = None,
    code: str | None = None,
) -> MonitorOverview:
    """聚合当前用户自选股监控数据，单只失败不会中断整体响应。"""
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    groups = watchlist_service.get_groups_with_stocks(db, user_id)
    groups = _filter_groups(groups, group_id)
    watch_items = [
        _watch_item_payload(group, item)
        for group in groups
        for item in getattr(group, "stocks", [])
    ]
    if code:
        watch_items = [item for item in watch_items if item["code"] == code]

    market, errors = _load_market(market_loader or get_market_summary_with_meta, current_time)
    unique_codes = list(dict.fromkeys(item["code"] for item in watch_items))
    snapshots = _load_snapshots(
        unique_codes,
        days,
        snapshot_loader or get_monitor_snapshot,
        current_time,
    )

    items = [
        _build_monitor_item(payload, snapshots.get(payload["code"]), market)
        for payload in watch_items
    ]
    items.sort(key=_item_sort_key)
    summary = _build_summary(items)
    action_queue = build_action_queue(items)
    return MonitorOverview(
        as_of=_oldest_data_time(market, snapshots, current_time),
        market=market,
        summary=summary,
        items=items,
        action_queue=action_queue,
        errors=errors,
    )


def _filter_groups(groups, group_id: str):
    if group_id == "all":
        return groups
    try:
        target_id = int(group_id)
    except (TypeError, ValueError) as exc:
        raise MonitorGroupNotFound(f"分组不存在: {group_id}") from exc
    filtered = [group for group in groups if group.id == target_id]
    if not filtered:
        raise MonitorGroupNotFound(f"分组不存在: {group_id}")
    return filtered


def _watch_item_payload(group, item) -> dict:
    return {
        "watchlist_item_id": item.id,
        "group_id": group.id,
        "group_name": group.name,
        "code": str(item.stock_code),
        "name": item.stock_name,
        "cost": float(item.cost or 0),
        "remark": item.remark or "",
    }


def _load_market(loader: Callable[[], object], now: datetime):
    try:
        loaded = loader()
        from_cache = False
        fetched_at = None
        if isinstance(loaded, tuple) and len(loaded) >= 3:
            summary, from_cache, fetched_at = loaded[:3]
        elif isinstance(loaded, tuple) and len(loaded) == 2 and isinstance(loaded[1], bool):
            summary, from_cache = loaded
        else:
            summary = loaded
        if summary is None:
            raise RuntimeError("市场概览数据不可用")
        return MonitorMarket(
            environment=classify_market_environment(summary),
            summary=summary,
            as_of=fetched_at or now,
            stale=from_cache,
        ), []
    except Exception as exc:
        return MonitorMarket(environment="未知", summary=None, stale=True), [
            MonitorError(scope="market", message=str(exc), retryable=True)
        ]


def _load_snapshots(codes, days, loader, now):
    result: dict[str, MonitorSnapshot | None] = {}
    with ThreadPoolExecutor(max_workers=MONITOR_MAX_WORKERS) as executor:
        futures = {code: executor.submit(_load_one_snapshot, code, days, loader, now) for code in codes}
        for code, future in futures.items():
            try:
                result[code] = future.result()
            except Exception as exc:
                result[code] = MonitorSnapshot(code=code, errors=[str(exc)])
    return result


def _load_one_snapshot(code, days, loader, now):
    key = (code, days)
    with _cache_lock:
        cached = _snapshot_cache.get(key)
        if cached and cached.expires_at > now:
            return _mark_cached_snapshot(cached.value)
    try:
        snapshot = loader(code, days)
    except Exception as exc:
        if cached:
            return _mark_cached_snapshot(cached.value).model_copy(update={"errors": [str(exc)]})
        return MonitorSnapshot(code=code, errors=[str(exc)])
    if snapshot.fetched_at is None:
        snapshot = snapshot.model_copy(update={"fetched_at": now})
    with _cache_lock:
        _snapshot_cache[key] = CacheEntry(value=snapshot, expires_at=now + MONITOR_CACHE_TTL)
    return snapshot


def _mark_cached_snapshot(snapshot: MonitorSnapshot) -> MonitorSnapshot:
    """复制缓存快照，避免把缓存结果误标为实时数据。"""
    if snapshot.quote is None:
        return snapshot
    quote = snapshot.quote.model_copy(update={"source": "cache", "stale": True})
    return snapshot.model_copy(update={"quote": quote})


def _oldest_data_time(market: MonitorMarket, snapshots, fallback: datetime) -> datetime:
    """顶层时间取可见数据中最旧的真实抓取时间，避免请求时间掩盖延迟数据。"""
    values = []
    market_time = _as_datetime(market.as_of)
    if market_time:
        values.append(market_time)
    for snapshot in snapshots.values():
        if snapshot and snapshot.fetched_at:
            values.append(_as_datetime(snapshot.fetched_at))
    return min(values) if values else fallback


def _as_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _build_monitor_item(payload, snapshot, market):
    if snapshot is None:
        snapshot = MonitorSnapshot(code=payload["code"], errors=["行情或指标数据不可用"])
    quote = snapshot.quote
    if quote and snapshot.errors:
        quote = quote.model_copy(update={"stale": True})
    cost_return = None
    if quote and quote.price is not None and payload["cost"] > 0:
        cost_return = (quote.price / payload["cost"] - 1) * 100
    market_change = getattr(getattr(market, "summary", None), "sh_change_pct", None)
    relative_strength = None
    if quote and quote.change_pct is not None and market_change is not None:
        relative_strength = quote.change_pct - market_change
    metrics = snapshot.metrics or MonitorMetrics()
    metrics = metrics.model_copy(update={
        "cost_return_pct": round(cost_return, 2) if cost_return is not None else None,
        "relative_strength_vs_sh_pct": round(relative_strength, 2) if relative_strength is not None else None,
    })
    rows = snapshot.rows or snapshot.kline
    analysis = analyze_signals(rows, cost_return)
    if snapshot.errors:
        if quote is None or len(rows) < 2:
            analysis = analysis.model_copy(update={"status": "error"})
        elif analysis.status != "error":
            stale_signal = SignalItem(
                code="data-stale",
                kind="attention",
                label="行情数据已延迟",
                detail=snapshot.errors[0],
            )
            analysis = analysis.model_copy(
                update={"status": "attention", "signals": [stale_signal, *analysis.signals]}
            )
    return MonitorItem(
        watchlist_item_id=payload["watchlist_item_id"],
        group_id=payload["group_id"],
        group_name=payload["group_name"],
        code=payload["code"],
        name=payload["name"],
        cost=payload["cost"],
        remark=payload["remark"],
        quote=quote,
        indicators=snapshot.indicators,
        metrics=metrics,
        status=analysis.status,
        signals=analysis.signals,
        sparkline=snapshot.sparkline,
        errors=snapshot.errors,
    )


def _item_sort_key(item: MonitorItem):
    status_order = {"attention": 0, "strong": 1, "neutral": 2, "error": 3}
    return status_order.get(item.status, 4), -len(item.signals), item.code


def _build_summary(items: list[MonitorItem]) -> MonitorSummary:
    changes = [item.quote.change_pct for item in items if item.quote and item.quote.change_pct is not None]
    relative = [
        item.metrics.relative_strength_vs_sh_pct
        for item in items
        if item.metrics and item.metrics.relative_strength_vs_sh_pct is not None
    ]
    return MonitorSummary(
        stock_count=len(items),
        rising_count=sum(bool(item.quote and item.quote.change_pct and item.quote.change_pct > 0) for item in items),
        falling_count=sum(bool(item.quote and item.quote.change_pct and item.quote.change_pct < 0) for item in items),
        strong_count=sum(item.status == "strong" for item in items),
        attention_count=sum(item.status == "attention" for item in items),
        error_count=sum(item.status == "error" for item in items),
        average_change_pct=round(sum(changes) / len(changes), 2) if changes else None,
        average_relative_strength_pct=round(sum(relative) / len(relative), 2) if relative else None,
    )
