"""
复盘报告相关 Pydantic 模型。
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel


class StockReportResponse(BaseModel):
    id: int
    daily_report_id: int
    stock_code: str
    stock_name: str
    change_pct: float
    close_price: float
    analysis_text: str
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HighlightItem(BaseModel):
    stock_code: str
    stock_name: str
    reason: str


class DailyReportResponse(BaseModel):
    id: int
    user_id: int
    report_date: date
    market_summary: str
    highlights: List[HighlightItem] = []
    risk_notes: str
    status: str
    stock_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    stock_reports: List[StockReportResponse] = []

    model_config = {"from_attributes": True}


class DailyReportListItem(BaseModel):
    """列表页用的精简版，不包含 stock_reports 详情。"""
    id: int
    report_date: date
    status: str
    stock_count: int
    market_summary: str  # 截断版或完整版
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedDailyReports(BaseModel):
    items: List[DailyReportListItem]
    total: int
    page: int
    page_size: int
