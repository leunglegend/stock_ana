"""
自选股数据模型：分组 + 明细。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class WatchlistGroup(Base):
    __tablename__ = "watchlist_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    stocks = relationship("WatchlistItem", back_populates="group", cascade="all, delete-orphan", order_by="WatchlistItem.sort_order")

    __table_args__ = (
        Index("idx_group_user_sort", "user_id", "sort_order"),
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("watchlist_groups.id"), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(20), nullable=False)
    cost = Column(Float, default=0.0)
    remark = Column(String(200), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("WatchlistGroup", back_populates="stocks")

    __table_args__ = (
        Index("idx_item_group_sort", "group_id", "sort_order"),
    )
