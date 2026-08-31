"""盘中监控接口模型。"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.schemas import KLineItem, MarketSummary


SignalKind = Literal["positive", "attention", "info"]
SignalStatus = Literal["attention", "strong", "neutral", "error"]


class SignalItem(BaseModel):
    code: str
    kind: SignalKind
    label: str
    detail: str = ""


class SignalAnalysis(BaseModel):
    status: SignalStatus
    signals: list[SignalItem] = Field(default_factory=list)
    note: str = ""
    as_of: str | None = None


class MonitorQuote(BaseModel):
    price: float | None = None
    change_pct: float | None = None
    change_amount: float | None = None
    volume: float | None = None
    amount: float | None = None
    source: str | None = None
    as_of: str | datetime | None = None
    stale: bool = False


class MonitorIndicators(BaseModel):
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    dif: float | None = None
    dea: float | None = None
    macd: float | None = None
    rsi6: float | None = None
    rsi12: float | None = None
    rsi24: float | None = None
    high20_distance_pct: float | None = None


class MonitorMetrics(BaseModel):
    cost_return_pct: float | None = None
    relative_strength_vs_sh_pct: float | None = None
    return_5d_pct: float | None = None
    return_20d_pct: float | None = None


class MonitorItem(BaseModel):
    watchlist_item_id: int | None = None
    group_id: int | None = None
    group_name: str | None = None
    code: str
    name: str
    cost: float | None = None
    remark: str | None = None
    quote: MonitorQuote | None = None
    indicators: MonitorIndicators | None = None
    metrics: MonitorMetrics | None = None
    status: SignalStatus = "error"
    signals: list[SignalItem] = Field(default_factory=list)
    sparkline: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ActionQueueItem(BaseModel):
    code: str
    name: str
    priority: Literal["high", "medium"]
    reasons: list[str] = Field(default_factory=list)


class MonitorSummary(BaseModel):
    stock_count: int = 0
    rising_count: int = 0
    falling_count: int = 0
    strong_count: int = 0
    attention_count: int = 0
    error_count: int = 0
    average_change_pct: float | None = None
    average_relative_strength_pct: float | None = None


class MonitorMarket(BaseModel):
    environment: Literal["偏强", "偏弱", "分化", "未知"] = "未知"
    summary: MarketSummary | None = None
    as_of: str | datetime | None = None
    stale: bool = False


class MonitorError(BaseModel):
    scope: str
    message: str
    retryable: bool = False


class MonitorOverview(BaseModel):
    as_of: str | datetime | None = None
    market: MonitorMarket | None = None
    summary: MonitorSummary = Field(default_factory=MonitorSummary)
    items: list[MonitorItem] = Field(default_factory=list)
    action_queue: list[ActionQueueItem] = Field(default_factory=list)
    errors: list[MonitorError] = Field(default_factory=list)


class MonitorSnapshot(BaseModel):
    """内部单股票快照，供监控聚合服务复用。"""

    code: str
    name: str | None = None
    rows: list[KLineItem] = Field(default_factory=list)
    kline: list[KLineItem] = Field(default_factory=list)
    quote: MonitorQuote | None = None
    indicators: MonitorIndicators | None = None
    metrics: MonitorMetrics | None = None
    sparkline: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    fetched_at: datetime | None = None
