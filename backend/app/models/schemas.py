"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Any, List, Optional


class StockInfo(BaseModel):
    """股票基本信息"""
    code: str
    name: str
    price: float
    change_pct: float
    change_amount: float
    open: float
    pre_close: float
    high: float
    low: float
    volume: float
    amount: float


class KLineItem(BaseModel):
    """K线数据项"""
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    # MACD
    dif: Optional[float] = None
    dea: Optional[float] = None
    macd: Optional[float] = None
    # KDJ
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None
    # RSI
    rsi6: Optional[float] = None
    rsi12: Optional[float] = None
    rsi24: Optional[float] = None


class KLineData(BaseModel):
    """K线数据"""
    code: str
    name: str
    kline: List[KLineItem]


class FinancialData(BaseModel):
    """财务数据"""
    code: str
    name: str
    pe: Optional[float] = None          # 市盈率
    pb: Optional[float] = None          # 市净率
    total_mv: Optional[float] = None    # 总市值(亿)
    roe: Optional[float] = None         # ROE
    net_profit: Optional[float] = None  # 净利润(亿)
    revenue: Optional[float] = None     # 营业收入(亿)
    gross_margin: Optional[float] = None  # 毛利率
    net_margin: Optional[float] = None    # 净利率
    report_date: Optional[str] = None     # 报告期


class StockSearchItem(BaseModel):
    """搜索结果项"""
    code: str
    name: str


class StockDecisionConclusion(BaseModel):
    """个股决策结论。"""
    action: str = "hold"
    label: str = "观望"
    score: int = 0
    rationale: str = ""


class StockDecisionReport(BaseModel):
    """按当前行情生成的临时结构化决策报告。"""
    code: str
    name: str
    generated_at: str
    as_of: Optional[str] = None
    conclusion: StockDecisionConclusion
    trend: dict[str, Any] = Field(default_factory=dict)
    levels: dict[str, Any] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    catalysts: List[str] = Field(default_factory=list)
    sentiment: dict[str, Any] = Field(default_factory=dict)
    fundamentals: dict[str, Any] = Field(default_factory=dict)
    latest_developments: dict[str, Any] = Field(default_factory=dict)
    checklist: List[str] = Field(default_factory=list)
    signals: List[dict[str, Any]] = Field(default_factory=list)
    analysis_markdown: str = ""
    data_quality: dict[str, Any] = Field(default_factory=dict)


class DecisionReportRequest(BaseModel):
    """决策报告请求模型（保留扩展入口）。"""
    code: str


class BoardInfo(BaseModel):
    """板块信息"""
    name: str                          # 板块名称
    change_pct: float                  # 涨跌幅(%)
    change_amount: float = 0           # 涨跌额
    total_turnover: float = 0          # 总市值/总成交额（单位：亿）
    turnover_rate: float = 0           # 换手率(%)
    leading_stock: str = ""            # 领涨股
    leading_change: float = 0          # 领涨股涨跌幅(%)
    stock_count: int = 0               # 股票总数
    rise_count: int = 0                # 上涨家数
    fall_count: int = 0                # 下跌家数


class BoardStock(BaseModel):
    """板块成分股"""
    code: str
    name: str
    price: float
    change_pct: float
    change_amount: float = 0
    turnover_rate: float = 0
    pe: Optional[float] = None
    total_mv: Optional[float] = None


class MarketSummary(BaseModel):
    """市场概览"""
    # 主要指数
    sh_index: Optional[float] = None    # 上证指数
    sh_change_pct: Optional[float] = None  # 上证指数涨跌幅(%)
    sh_change_amount: Optional[float] = None  # 上证指数涨跌点数
    sz_index: Optional[float] = None    # 深证成指
    sz_change_pct: Optional[float] = None  # 深证成指涨跌幅(%)
    sz_change_amount: Optional[float] = None  # 深证成指涨跌点数
    cyb_index: Optional[float] = None   # 创业板指
    cyb_change_pct: Optional[float] = None  # 创业板指涨跌幅(%)
    cyb_change_amount: Optional[float] = None  # 创业板指涨跌点数
    # 市场统计
    rise_count: int = 0                 # 上涨家数
    fall_count: int = 0                 # 下跌家数
    flat_count: int = 0                 # 平盘家数
    limit_up_count: int = 0             # 涨停数
    limit_down_count: int = 0           # 跌停数
    total_amount: float = 0             # 两市成交额(亿)
    # AI 总结
    ai_summary: str = ""                # AI 一句话总结


# ===== 美股复盘（US market，收盘口径）=====

class UsIndexQuote(BaseModel):
    """美股指数收盘快照（新浪静态日线末两根 bar 自算涨跌）。"""
    symbol: str                # SPX / DJI / IXIC / NDX / SOX
    name: str                  # 中文名
    value: float               # 收盘点位
    change_amount: float = 0   # 涨跌点
    change_pct: float = 0      # 涨跌幅(%)


class UsSector(BaseModel):
    """美股 GICS 一级行业板块（标普500成分等权聚合，非官方板块指数）。"""
    name: str                                  # 中文板块名
    name_en: str = ""                          # 英文板块名（GICS）
    change_pct: float = 0                      # 成分当日涨跌幅等权平均(%)
    leading_symbol: str = ""                   # 领涨成分 ticker
    leading_name: str = ""                     # 领涨成分名（英文）
    leading_change_pct: float = 0              # 领涨成分涨跌幅(%)
    advancers: int = 0                         # 板块内上涨成分数
    decliners: int = 0                         # 板块内下跌成分数
    constituent_count: int = 0                 # 板块有效行情成分数
    method: str = "equal_weight"               # 口径: equal_weight


class UsConstituent(BaseModel):
    """标普500 成分（板块成员）收盘行情。"""
    symbol: str                # 字母 ticker
    name: str                  # 英文名（本期无稳定中文个股名来源）
    price: float               # 收盘价
    change_amount: float = 0   # 涨跌额
    change_pct: float = 0      # 涨跌幅(%)


class UsSummary(BaseModel):
    """美股收盘复盘概览（Dashboard 卡与页面摘要区共用一个源）。"""
    as_of: str = ""                              # 美东最近交易日（数据自报）
    updated_at: str = ""                         # 北京时间取数时间
    breadth_scope: str = "标普500成分口径"        # 广度统计范围说明
    indices: List[UsIndexQuote] = []
    advancers: int = 0                           # 成分内上涨数
    decliners: int = 0                           # 成分内下跌数
    unchanged: int = 0                           # 成分内平盘数
    top_gainers: List[UsSector] = []             # 领涨板块 Top3（降序前 3）
    top_losers: List[UsSector] = []              # 领跌板块 Top3（升序前 3）
