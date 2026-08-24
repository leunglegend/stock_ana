"""
复盘报告数据模型：日报 + 个股分析。
"""

from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_date = Column(Date, nullable=False)
    market_summary = Column(Text, default="")
    highlights = Column(JSON, default=list)  # [{stock_code, stock_name, reason}]
    risk_notes = Column(Text, default="")
    status = Column(String(20), default="pending")  # pending / generating / completed / failed
    stock_count = Column(Integer, default=0)
    error_msg = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    stock_reports = relationship("StockReport", back_populates="daily_report", cascade="all, delete-orphan", order_by="StockReport.change_pct.desc()")

    __table_args__ = (
        Index("idx_report_user_date", "user_id", "report_date"),
        UniqueConstraint("user_id", "report_date", name="uq_user_report_date"),
    )


class StockReport(Base):
    __tablename__ = "stock_reports"

    id = Column(Integer, primary_key=True, index=True)
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(20), nullable=False)
    change_pct = Column(Float, default=0.0)
    close_price = Column(Float, default=0.0)
    analysis_text = Column(Text, default="")
    summary = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    daily_report = relationship("DailyReport", back_populates="stock_reports")
