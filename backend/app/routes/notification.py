"""
通知相关 API 路由。
所有接口需登录。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    PaginatedNotifications,
    UnreadCountResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("", response_model=PaginatedNotifications, summary="获取通知列表")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = notification_service.get_notifications(
        db, current_user.id, page, page_size, unread_only
    )
    return PaginatedNotifications(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/unread-count", response_model=UnreadCountResponse, summary="未读数量")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = notification_service.get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.put("/{notif_id}/read", response_model=NotificationResponse, summary="标记已读")
def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = notification_service.mark_as_read(db, current_user.id, notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在")
    return notif


@router.put("/read-all", summary="全部已读")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = notification_service.mark_all_as_read(db, current_user.id)
    return {"success": True, "count": count}
