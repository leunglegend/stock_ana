"""
盘后复盘报告服务：生成 + 查询。
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import DailyReport, StockReport
from app.models.watchlist import WatchlistGroup, WatchlistItem
from app.services import watchlist_service

logger = logging.getLogger(__name__)

AI_ERROR_MARKERS = (
    "AI 服务暂不可用",
    "AI 分析服务暂不可用",
    "AI 分析出错",
    "AI 盘后分析出错",
    "AI 日报总览出错",
    "AuthenticationError",
    "unexpected keyword argument",
)
REPORT_STATUSES = frozenset({"all", "completed", "generating", "failed", "pending"})
REPORT_DAYS = frozenset({"7", "30", "90", "all"})


def is_report_usable(report: DailyReport) -> bool:
    """只有包含真实 AI 内容的完成态报告才可复用。"""
    if report.status != "completed" or report.error_msg or not report.market_summary.strip():
        return False
    stock_reports = list(report.stock_reports or [])
    if not stock_reports:
        return False
    content = [report.market_summary]
    content.extend(item.analysis_text or "" for item in stock_reports)
    content.extend(item.summary or "" for item in stock_reports)
    return not any(marker in text for marker in AI_ERROR_MARKERS for text in content)


def get_reports(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: str = "all",
    days: str = "all",
) -> Tuple[List[DailyReport], int]:
    """按状态和日期范围筛选后分页获取用户复盘报告。"""
    if status not in REPORT_STATUSES or days not in REPORT_DAYS:
        raise ValueError("invalid report filters")

    query = db.query(DailyReport).filter(DailyReport.user_id == user_id)
    if status != "all":
        query = query.filter(DailyReport.status == status)
    if days != "all":
        start_date = date.today() - timedelta(days=int(days) - 1)
        query = query.filter(DailyReport.report_date >= start_date)

    total = query.count()
    items = (
        query.order_by(DailyReport.report_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_report_detail(db: Session, user_id: int, report_id: int) -> Optional[DailyReport]:
    """获取报告详情（含个股分析）。"""
    report = (
        db.query(DailyReport)
        .filter(DailyReport.id == report_id, DailyReport.user_id == user_id)
        .first()
    )
    return report


def get_report_by_date(db: Session, user_id: int, report_date: date) -> Optional[DailyReport]:
    """根据日期获取报告。"""
    return (
        db.query(DailyReport)
        .filter(DailyReport.user_id == user_id, DailyReport.report_date == report_date)
        .first()
    )


def get_all_users_with_watchlist(db: Session) -> List[int]:
    """获取所有有自选股的用户 ID 列表（用于定时任务遍历）。"""
    user_ids = (
        db.query(WatchlistGroup.user_id)
        .join(WatchlistItem, WatchlistItem.group_id == WatchlistGroup.id)
        .distinct()
        .all()
    )
    return [row[0] for row in user_ids]


def create_pending_report(db: Session, user_id: int, report_date: date) -> DailyReport:
    """创建一个 pending 状态的报告记录。"""
    # 检查是否已存在
    existing = get_report_by_date(db, user_id, report_date)
    if existing:
        # 重置为 pending，重新生成
        existing.status = "pending"
        existing.market_summary = ""
        existing.highlights = []
        existing.risk_notes = ""
        existing.error_msg = ""
        existing.stock_count = 0
        existing.completed_at = None
        # 删除旧的个股分析
        db.query(StockReport).filter(StockReport.daily_report_id == existing.id).delete()
        db.commit()
        db.refresh(existing)
        return existing

    report = DailyReport(
        user_id=user_id,
        report_date=report_date,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def update_report_status(
    db: Session, report_id: int, status: str, error_msg: str = ""
) -> None:
    """更新报告状态。"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if report:
        report.status = status
        if error_msg:
            report.error_msg = error_msg
        if status == "completed":
            report.completed_at = datetime.utcnow()
        db.commit()


def save_stock_report(
    db: Session,
    daily_report_id: int,
    stock_code: str,
    stock_name: str,
    change_pct: float,
    close_price: float,
    analysis_text: str,
    summary: str,
) -> StockReport:
    """保存个股分析结果。"""
    item = StockReport(
        daily_report_id=daily_report_id,
        stock_code=stock_code,
        stock_name=stock_name,
        change_pct=change_pct,
        close_price=close_price,
        analysis_text=analysis_text,
        summary=summary,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    # 更新日报 stock_count
    report = db.query(DailyReport).filter(DailyReport.id == daily_report_id).first()
    if report:
        report.stock_count = (
            db.query(StockReport).filter(StockReport.daily_report_id == daily_report_id).count()
        )
        db.commit()
    return item


def save_report_summary(
    db: Session,
    report_id: int,
    market_summary: str,
    highlights: List[dict],
    risk_notes: str,
) -> None:
    """保存报告的整体分析（市场总览 + 关注重点 + 风险提示）。"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if report:
        report.market_summary = market_summary
        report.highlights = highlights
        report.risk_notes = risk_notes
        db.commit()


def generate_daily_report_for_user(
    db: Session, user_id: int, report_date: date
) -> Optional[DailyReport]:
    """
    为指定用户生成一天的复盘报告（同步版本）。
    这是核心生成函数，返回生成好的报告，失败返回 None。

    流程：
    1. 获取用户自选股
    2. 创建或复用 pending/generating report
    3. 获取市场概览数据
    4. 逐只股票获取行情 + K 线 + AI 分析
    5. 生成整体市场点评 + 关注重点
    6. 标记 completed
    """
    from app.services.stock_data import get_stock_info, get_kline_data
    from app.services.market_data import get_market_summary
    from app.services.ai_analyst import generate_stock_daily_analysis, generate_daily_report_overview

    # 1. 获取自选股
    stocks = watchlist_service.get_user_watchlist_stocks(db, user_id)
    if not stocks:
        logger.info("用户 %s 没有自选股，跳过复盘生成", user_id)
        return None

    # 2. 获取或创建报告
    existing = get_report_by_date(db, user_id, report_date)
    if existing and existing.status in ("pending", "generating"):
        # 已有 pending/generating 报告，直接复用（避免竞态重置）
        report = existing
        report.status = "generating"
        report.error_msg = ""
        db.commit()
    elif existing and is_report_usable(existing):
        # 已完成且内容有效，不再重新生成
        return existing
    else:
        # 不存在或失败，创建新的
        report = create_pending_report(db, user_id, report_date)
        report.status = "generating"
        db.commit()

    try:
        # 3. 获取市场概览
        try:
            market_data = get_market_summary()
        except Exception as e:
            logger.warning("获取市场概览失败: %s", e)
            market_data = None

        # 4. 逐只股票分析
        stock_results = []
        for stock_code, stock_name in stocks:
            try:
                # 获取行情
                quote = get_stock_info(stock_code)
                if quote is None:
                    logger.warning("获取股票 %s 行情失败，跳过", stock_code)
                    continue
                change_pct = float(getattr(quote, "change_pct", 0) or 0.0)
                close_price = float(getattr(quote, "price", 0) or 0.0)

                # 获取近 30 日 K 线
                try:
                    kline = get_kline_data(stock_code, period="daily", days=30)
                except Exception:
                    kline = None

                # AI 分析（同步调用）
                analysis_text, summary = generate_stock_daily_analysis(
                    stock_code, stock_name, quote, kline
                )

                # 保存
                save_stock_report(
                    db, report.id, stock_code, stock_name,
                    change_pct, close_price, analysis_text, summary
                )
                stock_results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "change_pct": change_pct,
                    "summary": summary,
                })

            except Exception as e:
                logger.error("分析股票 %s 失败: %s", stock_code, e)
                continue

        if not stock_results:
            update_report_status(db, report.id, "failed", "所有股票分析均失败")
            return None

        # 5. 生成整体复盘
        try:
            market_summary_text, highlights, risk_notes = generate_daily_report_overview(
                stock_results, market_data
            )
            save_report_summary(db, report.id, market_summary_text, highlights, risk_notes)
        except Exception as e:
            logger.warning("生成整体复盘失败: %s", e)
            # 整体失败不影响个股结果，留空即可

        # 6. 标记完成
        update_report_status(db, report.id, "completed")
        db.refresh(report)
        return report

    except Exception as e:
        logger.error("生成复盘报告失败 (user=%s, date=%s): %s", user_id, report_date, e)
        update_report_status(db, report.id, "failed", str(e)[:500])
        return None
