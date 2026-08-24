"""
复盘报告相关 API 路由。
所有接口需登录。
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import (
    DailyReportResponse,
    DailyReportListItem,
    PaginatedDailyReports,
)
from app.services import report_service, notification_service

router = APIRouter(prefix="/api/reports", tags=["复盘报告"])


@router.get("", response_model=PaginatedDailyReports, summary="复盘报告列表")
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分页获取当前用户的复盘报告列表。"""
    items, total = report_service.get_reports(db, current_user.id, page, page_size)
    return PaginatedDailyReports(
        items=[DailyReportListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=DailyReportResponse, summary="报告详情")
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单份复盘报告详情（含个股分析）。"""
    report = report_service.get_report_detail(db, current_user.id, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


def _run_generate_task(user_id: int, report_date: date):
    """在后台线程中运行报告生成任务。"""
    db = SessionLocal()
    try:
        report = report_service.generate_daily_report_for_user(db, user_id, report_date)
        if report and report.status == "completed":
            # 生成通知
            notification_service.create_notification(
                db,
                user_id=user_id,
                title=f"{report_date} 盘后复盘已生成",
                content=f"覆盖 {report.stock_count} 只自选股，点击查看详情",
                notification_type="report",
                ref_id=report.id,
            )
    finally:
        db.close()


@router.post("/generate", summary="手动生成今日复盘")
def generate_today(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发生成今日复盘报告（后台异步执行）。"""
    today = date.today()
    # 检查是否已有 completed 的报告
    existing = report_service.get_report_by_date(db, current_user.id, today)
    if existing and existing.status == "completed":
        return {"success": True, "report_id": existing.id, "message": "今日报告已存在"}
    if existing and existing.status == "generating":
        return {"success": True, "report_id": existing.id, "message": "正在生成中..."}

    # 先创建 pending 记录（确保在后台任务启动前已存在）
    report = report_service.create_pending_report(db, current_user.id, today)

    # 再添加后台任务
    background_tasks.add_task(_run_generate_task, current_user.id, today)

    return {"success": True, "report_id": report.id, "message": "正在生成中..."}
