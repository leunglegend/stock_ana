"""
自选股相关 API 路由。
所有接口需登录。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.watchlist import (
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistGroupResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
    WatchlistSyncRequest,
)
from app.services import watchlist_service

router = APIRouter(prefix="/api/watchlist", tags=["自选股"])


# ---------- 分组 ----------

@router.get("/groups", response_model=List[WatchlistGroupResponse], summary="获取自选股分组列表")
def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户所有分组（含分组下的股票）。"""
    groups = watchlist_service.get_groups_with_stocks(db, current_user.id)
    return groups


@router.post("/groups", response_model=WatchlistGroupResponse, summary="新建分组")
def create_group(
    data: WatchlistGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = watchlist_service.create_group(db, current_user.id, data)
    return group


@router.put("/groups/{group_id}", response_model=WatchlistGroupResponse, summary="更新分组")
def update_group(
    group_id: int,
    data: WatchlistGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = watchlist_service.update_group(db, current_user.id, group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@router.delete("/groups/{group_id}", summary="删除分组")
def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = watchlist_service.delete_group(db, current_user.id, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {"success": True}


# ---------- 股票 ----------

@router.post("/items", response_model=WatchlistItemResponse, summary="添加自选股")
def add_item(
    data: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = watchlist_service.add_item(db, current_user.id, data)
    if not item:
        raise HTTPException(status_code=400, detail="添加失败：分组不存在或股票已在列表中")
    return item


@router.put("/items/{item_id}", response_model=WatchlistItemResponse, summary="更新自选股")
def update_item(
    item_id: int,
    data: WatchlistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = watchlist_service.update_item(db, current_user.id, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="自选股不存在")
    return item


@router.delete("/items/{item_id}", summary="删除自选股")
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = watchlist_service.delete_item(db, current_user.id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="自选股不存在")
    return {"success": True}


# ---------- 同步 ----------

@router.post("/sync", response_model=List[WatchlistGroupResponse], summary="批量同步自选股")
def sync_watchlist(
    data: WatchlistSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从客户端批量导入自选股（用于首次登录同步 localStorage 数据）。"""
    groups = watchlist_service.sync_watchlist(db, current_user.id, data)
    return groups
