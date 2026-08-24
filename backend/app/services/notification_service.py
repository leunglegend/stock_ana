"""
通知服务：站内信管理。
"""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str = "",
    type: str = "system",
    ref_id: Optional[int] = None,
) -> Notification:
    """创建一条通知。"""
    notif = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=type,
        ref_id=ref_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_notifications(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> Tuple[List[Notification], int]:
    """分页获取通知列表。"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_unread_count(db: Session, user_id: int) -> int:
    """获取未读通知数量。"""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .count()
    )


def mark_as_read(db: Session, user_id: int, notif_id: int) -> bool:
    """标记单条通知为已读。"""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user_id,
    ).first()
    if not notif:
        return False
    notif.is_read = True
    db.commit()
    return True


def mark_all_as_read(db: Session, user_id: int) -> int:
    """标记所有通知为已读，返回已读数量。"""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .update({Notification.is_read: True})
    )
    db.commit()
    return count
