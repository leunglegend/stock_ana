"""
通知消息数据模型。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String(500), default="")
    notification_type = Column(String(20), default="system")  # report / system
    ref_id = Column(Integer, nullable=True)  # 关联 ID，如 report_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_notif_user_read_time", "user_id", "is_read", "created_at"),
    )
