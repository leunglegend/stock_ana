"""盘中监控聚合 API 路由。"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.monitor import MonitorOverview
from app.services import monitor_service


router = APIRouter(prefix="/api/monitor", tags=["盘中监控"])


@router.get("/overview", response_model=MonitorOverview, summary="获取盘中监控总览")
def overview(
    group_id: str = Query("all", pattern=r"^(all|[0-9]+)$"),
    days: Literal["30", "60", "90"] = Query("90"),
    code: str | None = Query(None, min_length=1, max_length=16),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户自选股的市场、行情和规则信号聚合结果。"""
    try:
        options = {"code": code} if code is not None else {}
        return monitor_service.build_monitor_overview(db, current_user.id, group_id, int(days), **options)
    except monitor_service.MonitorGroupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
