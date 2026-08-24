"""
自选股服务：分组和股票的增删改查。
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistGroup, WatchlistItem
from app.schemas.watchlist import (
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistSyncRequest,
)


# ---------- 分组 ----------

def get_groups_with_stocks(db: Session, user_id: int) -> List[WatchlistGroup]:
    """获取用户所有分组及其下的股票，按 sort_order 排序。"""
    groups = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.user_id == user_id)
        .order_by(WatchlistGroup.sort_order, WatchlistGroup.id)
        .all()
    )
    return groups


def create_group(db: Session, user_id: int, data: WatchlistGroupCreate) -> WatchlistGroup:
    """创建新分组。"""
    # 计算最大 sort_order
    max_order = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.user_id == user_id)
        .count()
    )
    group = WatchlistGroup(
        user_id=user_id,
        name=data.name.strip(),
        sort_order=max_order,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, user_id: int, group_id: int, data: WatchlistGroupUpdate) -> Optional[WatchlistGroup]:
    """更新分组名称。"""
    group = db.query(WatchlistGroup).filter(
        WatchlistGroup.id == group_id,
        WatchlistGroup.user_id == user_id,
    ).first()
    if not group:
        return None
    if data.name is not None:
        group.name = data.name.strip()
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, user_id: int, group_id: int) -> bool:
    """删除分组（及其下所有股票）。"""
    group = db.query(WatchlistGroup).filter(
        WatchlistGroup.id == group_id,
        WatchlistGroup.user_id == user_id,
    ).first()
    if not group:
        return False
    db.delete(group)
    db.commit()
    return True


# ---------- 股票 ----------

def add_item(db: Session, user_id: int, data: WatchlistItemCreate) -> Optional[WatchlistItem]:
    """向分组添加股票。如果已存在则返回 None。"""
    # 验证分组属于该用户
    group = db.query(WatchlistGroup).filter(
        WatchlistGroup.id == data.group_id,
        WatchlistGroup.user_id == user_id,
    ).first()
    if not group:
        return None

    # 检查是否已存在
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.group_id == data.group_id,
        WatchlistItem.stock_code == data.stock_code,
    ).first()
    if existing:
        return None

    max_order = db.query(WatchlistItem).filter(WatchlistItem.group_id == data.group_id).count()
    item = WatchlistItem(
        group_id=data.group_id,
        stock_code=data.stock_code,
        stock_name=data.stock_name,
        cost=data.cost,
        remark=data.remark,
        sort_order=max_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, user_id: int, item_id: int, data: WatchlistItemUpdate) -> Optional[WatchlistItem]:
    """更新自选股（成本/备注）。"""
    item = (
        db.query(WatchlistItem)
        .join(WatchlistGroup)
        .filter(
            WatchlistItem.id == item_id,
            WatchlistGroup.user_id == user_id,
        )
        .first()
    )
    if not item:
        return None
    if data.cost is not None:
        item.cost = data.cost
    if data.remark is not None:
        item.remark = data.remark
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, user_id: int, item_id: int) -> bool:
    """删除自选股。"""
    item = (
        db.query(WatchlistItem)
        .join(WatchlistGroup)
        .filter(
            WatchlistItem.id == item_id,
            WatchlistGroup.user_id == user_id,
        )
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


# ---------- 同步 ----------

def sync_watchlist(db: Session, user_id: int, data: WatchlistSyncRequest) -> List[WatchlistGroup]:
    """批量同步自选股（从 localStorage 导入）。"""
    if data.replace:
        # 清空现有数据（逐条删除以触发 ORM 级联，bulk delete 不触发级联）
        groups = db.query(WatchlistGroup).filter(WatchlistGroup.user_id == user_id).all()
        for g in groups:
            db.delete(g)
        db.commit()

    for i, g in enumerate(data.groups):
        group = WatchlistGroup(
            user_id=user_id,
            name=g.name.strip(),
            sort_order=i,
        )
        db.add(group)
        db.flush()  # 获取 group.id

        for j, s in enumerate(g.stocks):
            item = WatchlistItem(
                group_id=group.id,
                stock_code=s.stock_code,
                stock_name=s.stock_name,
                cost=s.cost,
                remark=s.remark,
                sort_order=j,
            )
            db.add(item)

    db.commit()
    return get_groups_with_stocks(db, user_id)


def get_user_watchlist_stocks(db: Session, user_id: int) -> List[tuple]:
    """获取用户所有自选股的 (code, name) 列表，用于复盘任务。"""
    items = (
        db.query(WatchlistItem.stock_code, WatchlistItem.stock_name)
        .join(WatchlistGroup)
        .filter(WatchlistGroup.user_id == user_id)
        .distinct(WatchlistItem.stock_code)
        .all()
    )
    return [(row.stock_code, row.stock_name) for row in items]
