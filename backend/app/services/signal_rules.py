"""统一的盘中技术信号规则。百分比数值均以百分点表示。"""

from math import isfinite
from typing import Literal, Sequence

from app.models.schemas import KLineItem, MarketSummary
from app.schemas.monitor import (
    ActionQueueItem,
    MonitorItem,
    SignalAnalysis,
    SignalItem,
)

RSI_OVERHEATED = 75.0
RSI_OVERSOLD = 25.0
DRAWDOWN_ATTENTION_PCT = -10.0
COST_GAIN_PCT = 15.0
COST_LOSS_PCT = -10.0

_HIGH_RISK_CODES = {
    "cost-loss",
    "drawdown-20d",
    "macd-death-cross",
}


def analyze_signals(
    rows: Sequence[KLineItem], cost_return_pct: float | None
) -> SignalAnalysis:
    valid_rows = [row for row in rows if _finite(row.close)]
    if len(valid_rows) < 2:
        return SignalAnalysis(status="error", note="有效 K 线数据不足")

    latest = valid_rows[-1]
    previous = valid_rows[-2]
    signals: list[SignalItem] = []
    _append_trend_signal(signals, latest)
    _append_macd_signal(signals, previous, latest)
    _append_rsi_signal(signals, latest)
    _append_position_signal(signals, valid_rows)
    _append_cost_signal(signals, cost_return_pct)

    status = _resolve_status(signals)
    return SignalAnalysis(
        status=status,
        signals=signals,
        note="" if signals else "暂无显著规则信号",
        as_of=latest.date,
    )


def classify_market_environment(
    summary: MarketSummary | None,
) -> Literal["偏强", "偏弱", "分化", "未知"]:
    if summary is None:
        return "未知"
    rise = getattr(summary, "rise_count", None)
    fall = getattr(summary, "fall_count", None)
    flat = getattr(summary, "flat_count", None)
    limit_up = getattr(summary, "limit_up_count", None)
    limit_down = getattr(summary, "limit_down_count", None)
    if any(value is None for value in (rise, fall, limit_up, limit_down)):
        return "未知"
    total = rise + fall + (flat or 0)
    if total <= 0:
        return "未知"
    if rise / total >= 0.6 and limit_up >= limit_down:
        return "偏强"
    if fall / total >= 0.6 and limit_down > limit_up:
        return "偏弱"
    return "分化"


def build_action_queue(items: Sequence[MonitorItem]) -> list[ActionQueueItem]:
    queue: list[ActionQueueItem] = []
    for item in items:
        if item.status == "error":
            queue.append(
                ActionQueueItem(
                    code=item.code,
                    name=item.name,
                    priority="high",
                    reasons=item.errors or ["行情或指标数据不可用"],
                )
            )
            continue
        risk_signals = [signal for signal in item.signals if signal.kind == "attention"]
        if not risk_signals:
            continue
        reasons = [
            f"{signal.label} {signal.detail}".strip()
            if signal.label
            else (signal.detail or signal.code)
            for signal in risk_signals
        ]
        priority = "high" if any(signal.code in _HIGH_RISK_CODES for signal in risk_signals) else "medium"
        queue.append(
            ActionQueueItem(code=item.code, name=item.name, priority=priority, reasons=reasons)
        )
    priority_order = {"high": 0, "medium": 1}
    return sorted(queue, key=lambda action: priority_order[action.priority])


def _append_trend_signal(signals: list[SignalItem], row: KLineItem) -> None:
    if not _finite(row.ma20):
        return
    if row.close < row.ma20:
        signals.append(SignalItem(code="trend-below-ma20", kind="attention", label="收盘价低于 MA20", detail=_detail("收盘", row.close, "MA20", row.ma20)))
    elif row.close > row.ma20 and _finite(row.ma5) and row.ma5 > row.ma20:
        signals.append(SignalItem(code="trend-above-ma20", kind="positive", label="价格位于 MA20 上方", detail=_detail("MA5", row.ma5, "MA20", row.ma20)))


def _append_macd_signal(signals: list[SignalItem], previous: KLineItem, latest: KLineItem) -> None:
    if not all(_finite(value) for value in (previous.dif, previous.dea, latest.dif, latest.dea)):
        return
    if previous.dif <= previous.dea and latest.dif > latest.dea:
        signals.append(SignalItem(code="macd-golden-cross", kind="positive", label="MACD 上穿", detail=_detail("DIF", latest.dif, "DEA", latest.dea)))
    elif previous.dif >= previous.dea and latest.dif < latest.dea:
        signals.append(SignalItem(code="macd-death-cross", kind="attention", label="MACD 下穿", detail=_detail("DIF", latest.dif, "DEA", latest.dea)))


def _append_rsi_signal(signals: list[SignalItem], row: KLineItem) -> None:
    if not _finite(row.rsi6):
        return
    if row.rsi6 >= RSI_OVERHEATED:
        signals.append(SignalItem(code="rsi-overheated", kind="attention", label="RSI6 进入过热区间", detail=f"RSI6 {row.rsi6:.2f}"))
    elif row.rsi6 <= RSI_OVERSOLD:
        signals.append(SignalItem(code="rsi-oversold", kind="info", label="RSI6 进入超卖区间", detail=f"RSI6 {row.rsi6:.2f}"))


def _append_position_signal(signals: list[SignalItem], rows: Sequence[KLineItem]) -> None:
    prior_window = rows[-21:-1]
    if len(prior_window) < 20:
        return
    highs = [row.high for row in prior_window if _finite(row.high)]
    if not highs:
        return
    latest = rows[-1]
    prior_high = max(highs)
    if prior_high <= 0:
        return
    distance_pct = (latest.close / prior_high - 1) * 100
    if latest.close >= prior_high:
        signals.append(SignalItem(code="breakout-20d", kind="positive", label="突破近 20 日高位", detail=f"高于前高 {distance_pct:+.1f}%"))
    elif distance_pct <= DRAWDOWN_ATTENTION_PCT:
        signals.append(SignalItem(code="drawdown-20d", kind="attention", label="距近 20 日高位回撤较大", detail=f"距前高 {distance_pct:+.1f}%"))


def _append_cost_signal(signals: list[SignalItem], cost_return_pct: float | None) -> None:
    if not _finite(cost_return_pct):
        return
    if cost_return_pct <= COST_LOSS_PCT:
        signals.append(SignalItem(code="cost-loss", kind="attention", label="低于记录成本超过 10%", detail=f"成本收益 {cost_return_pct:+.1f}%"))
    elif cost_return_pct >= COST_GAIN_PCT:
        signals.append(SignalItem(code="cost-gain", kind="positive", label="高于记录成本超过 15%", detail=f"成本收益 {cost_return_pct:+.1f}%"))


def _resolve_status(signals: Sequence[SignalItem]) -> Literal["attention", "strong", "neutral"]:
    if any(signal.kind == "attention" for signal in signals):
        return "attention"
    if sum(signal.kind == "positive" for signal in signals) >= 2:
        return "strong"
    return "neutral"


def _finite(value: float | None) -> bool:
    return value is not None and isfinite(value)


def _detail(left_name: str, left: float, right_name: str, right: float) -> str:
    return f"{left_name} {left:.2f} / {right_name} {right:.2f}"
