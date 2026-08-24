"""
自选股相关 Pydantic 模型。
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WatchlistItemBase(BaseModel):
    stock_code: str = Field(..., max_length=10)
    stock_name: str = Field(..., max_length=20)
    cost: float = 0.0
    remark: str = ""


class WatchlistItemCreate(WatchlistItemBase):
    group_id: int


class WatchlistItemUpdate(BaseModel):
    cost: Optional[float] = None
    remark: Optional[str] = None


class WatchlistItemResponse(WatchlistItemBase):
    id: int
    group_id: int
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistGroupBase(BaseModel):
    name: str = Field(..., max_length=50)


class WatchlistGroupCreate(WatchlistGroupBase):
    pass


class WatchlistGroupUpdate(BaseModel):
    name: Optional[str] = None


class WatchlistGroupResponse(WatchlistGroupBase):
    id: int
    user_id: int
    sort_order: int
    created_at: datetime
    stocks: List[WatchlistItemResponse] = []

    model_config = {"from_attributes": True}


class WatchlistSyncGroup(BaseModel):
    """同步用的分组数据（从 localStorage 导入）。"""
    id: str  # 前端的临时 id
    name: str
    stocks: List[WatchlistItemBase] = []


class WatchlistSyncRequest(BaseModel):
    groups: List[WatchlistSyncGroup]
    replace: bool = False  # 是否替换现有数据
