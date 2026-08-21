"""
数据模型定义
"""
from pydantic import BaseModel
from typing import List, Optional


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


class AnalyzeRequest(BaseModel):
    """分析请求"""
    code: str


class BoardInfo(BaseModel):
    """板块信息"""
    name: str                          # 板块名称
    change_pct: float                  # 涨跌幅(%)
    change_amount: float = 0           # 涨跌额
    total_turnover: float = 0          # 总市值/成交额
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
