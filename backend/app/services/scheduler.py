"""
定时任务调度器。

使用 APScheduler BackgroundScheduler，在 FastAPI 启动时启动。
主要任务：盘后复盘（交易日 15:30）
"""

import asyncio
import logging
from datetime import date
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.services import report_service, notification_service

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def run_daily_report_job():
    """
    盘后复盘定时任务。
    遍历所有有自选股的用户，为每个用户生成当日复盘报告。
    """
    logger.info("开始执行盘后复盘定时任务")
    today = date.today()

    db = SessionLocal()
    try:
        user_ids = report_service.get_all_users_with_watchlist(db)
        logger.info("找到 %s 个有自选股的用户", len(user_ids))

        for user_id in user_ids:
            try:
                # 检查是否已生成
                existing = report_service.get_report_by_date(db, user_id, today)
                if existing and existing.status == "completed":
                    logger.info("用户 %s 今日报告已存在，跳过", user_id)
                    continue

                # 生成报告（同步调用 async 函数）
                report = asyncio.run(
                    report_service.generate_daily_report_for_user(db, user_id, today)
                )

                if report and report.status == "completed":
                    # 发送通知
                    notification_service.create_notification(
                        db,
                        user_id=user_id,
                        title=f"{today} 盘后复盘已生成",
                        content=f"覆盖 {report.stock_count} 只自选股，点击查看详情",
                        type="report",
                        ref_id=report.id,
                    )
                    logger.info("用户 %s 复盘报告生成完成，%s 只股票", user_id, report.stock_count)
                else:
                    logger.warning("用户 %s 复盘报告生成失败", user_id)

            except Exception as e:
                logger.error("生成用户 %s 复盘报告异常: %s", user_id, e, exc_info=True)
                continue

    finally:
        db.close()

    logger.info("盘后复盘定时任务执行完毕")


def start_scheduler():
    """启动定时任务调度器。"""
    global _scheduler
    if not settings.scheduler_enabled:
        logger.info("定时任务已禁用，跳过启动")
        return

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # 盘后复盘：周一到周五 15:30
    # 从 settings.daily_report_cron 解析 cron 表达式
    cron_parts = settings.daily_report_cron.strip().split()
    if len(cron_parts) == 5:
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            timezone="Asia/Shanghai",
        )
    else:
        # 默认
        trigger = CronTrigger(
            minute="30", hour="15", day_of_week="mon-fri", timezone="Asia/Shanghai"
        )

    _scheduler.add_job(
        run_daily_report_job,
        trigger=trigger,
        id="daily_report_job",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("定时任务调度器已启动，盘后复盘 Cron: %s", settings.daily_report_cron)


def shutdown_scheduler():
    """关闭定时任务调度器。"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")
