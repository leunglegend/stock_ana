"""
通知相关 Pydantic 模型。
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    title: str
    content: str
    type: str
    ref_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    count: int
