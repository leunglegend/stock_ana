from app.models.schemas import KLineItem, MarketSummary
from app.schemas.monitor import MonitorItem, SignalItem
from app.services.signal_rules import (
    analyze_signals,
    build_action_queue,
    classify_market_environment,
)


def _row(**kwargs):
    values = dict(
        date="2026-08-30",
        open=10,
        close=10,
        high=10.2,
        low=9.8,
        volume=100,
    )
    values.update(kwargs)
    return KLineItem(**values)


def test_detects_trend_cross_rsi_and_cost_signals():
    rows = [
        _row(close=9.8, high=10.1, ma5=9.5, ma10=9.6, ma20=10.0, dif=0.2, dea=0.3, rsi6=40),
        _row(close=10.8, high=10.9, ma5=10.4, ma10=10.1, ma20=10.0, dif=0.5, dea=0.3, rsi6=78),
    ]

    result = analyze_signals(rows, cost_return_pct=-12.0)

    assert {item.code for item in result.signals} == {
        "trend-above-ma20",
        "macd-golden-cross",
        "rsi-overheated",
        "cost-loss",
    }
    assert result.status == "attention"


def test_detects_breakout_and_drawdown_using_twenty_day_window():
    rows = [_row(close=10, high=10 + i * 0.01, ma20=9.9, ma5=10.1, dif=0.2, dea=0.1, rsi6=50) for i in range(20)]
    rows.append(_row(close=10.3, high=10.4, ma20=9.9, ma5=10.1, dif=0.2, dea=0.1, rsi6=50))
    result = analyze_signals(rows, cost_return_pct=None)
    assert any(item.code == "breakout-20d" for item in result.signals)

    rows[-1] = _row(close=8.8, high=9.0, ma20=9.9, ma5=9.1, dif=0.2, dea=0.1, rsi6=50)
    result = analyze_signals(rows, cost_return_pct=None)
    assert any(item.code == "drawdown-20d" for item in result.signals)
    assert result.status == "attention"


def test_position_signal_ignores_missing_high_values():
    rows = [
        _row(close=10, high=10 + i * 0.01, ma20=9.9, ma5=10.1, dif=0.2, dea=0.1, rsi6=50)
        for i in range(20)
    ]
    rows[5] = _row(close=10, high=float("nan"), ma20=9.9, ma5=10.1, dif=0.2, dea=0.1, rsi6=50)
    rows.append(_row(close=10.3, high=10.4, ma20=9.9, ma5=10.1, dif=0.2, dea=0.1, rsi6=50))

    result = analyze_signals(rows, cost_return_pct=None)

    assert any(item.code == "breakout-20d" for item in result.signals)


def test_position_signal_skips_non_positive_prior_high():
    rows = [
        _row(close=0.5, high=0, ma20=0.4, ma5=0.45, dif=0.2, dea=0.1, rsi6=50)
        for _ in range(20)
    ]
    rows.append(_row(close=1, high=1, ma20=0.4, ma5=0.45, dif=0.2, dea=0.1, rsi6=50))

    result = analyze_signals(rows, cost_return_pct=None)

    assert not any(item.code in {"breakout-20d", "drawdown-20d"} for item in result.signals)


def test_returns_error_for_insufficient_kline():
    result = analyze_signals([], cost_return_pct=None)
    assert result.status == "error"
    assert result.signals == []

    result = analyze_signals([_row()], cost_return_pct=None)
    assert result.status == "error"


def test_classifies_market_environment():
    assert classify_market_environment(None) == "未知"
    assert classify_market_environment(MarketSummary()) == "未知"
    assert classify_market_environment(
        MarketSummary(rise_count=70, fall_count=30, flat_count=0, limit_up_count=10, limit_down_count=3)
    ) == "偏强"
    assert classify_market_environment(
        MarketSummary(rise_count=30, fall_count=70, flat_count=0, limit_up_count=2, limit_down_count=5)
    ) == "偏弱"
    assert classify_market_environment(
        MarketSummary(rise_count=50, fall_count=40, flat_count=10, limit_up_count=2, limit_down_count=2)
    ) == "分化"


def test_build_action_queue_sorts_high_before_medium():
    high = MonitorItem(
        watchlist_item_id=1,
        group_id=1,
        group_name="重点",
        code="000001",
        name="高风险",
        status="attention",
        signals=[SignalItem(code="cost-loss", kind="attention", label="低于成本", detail="-12.0%")],
    )
    medium = MonitorItem(
        watchlist_item_id=2,
        group_id=1,
        group_name="重点",
        code="000002",
        name="中风险",
        status="attention",
        signals=[SignalItem(code="trend-below-ma20", kind="attention", label="跌破 MA20", detail="")],
    )
    neutral = MonitorItem(
        watchlist_item_id=3,
        group_id=1,
        group_name="重点",
        code="000003",
        name="正常",
        status="neutral",
    )

    result = build_action_queue([medium, neutral, high])

    assert [item.code for item in result] == ["000001", "000002"]
    assert result[0].priority == "high"
    assert result[1].priority == "medium"
