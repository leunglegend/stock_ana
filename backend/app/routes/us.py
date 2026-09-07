"""美股复盘 API 路由（收盘口径，方案 B 聚合）。"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.models.schemas import UsConstituent, UsSector, UsSummary
from app.services import us_data
from app.services.us_cache import get_us_snapshot
from app.services.us_universe import get_sector_cns, load_us_constituents

router = APIRouter(prefix="/api/us", tags=["美股"])

# 摘要/卡片的静态口径说明（产品文案，后端随文档常量带出）
BREADTH_SCOPE = "标普500成分口径"


@router.get("/summary", response_model=UsSummary, summary="美股收盘复盘概览")
def get_us_summary():
    """Dashboard 卡片与页面摘要区共用：3 指数 + 成分广度 + 领涨/领跌板块。"""
    snap = get_us_snapshot()
    if not snap:
        raise HTTPException(status_code=503, detail="美股数据获取失败，请稍后重试")
    summary = us_data.compose_summary(snap.indices, snap.sectors, snap.as_of)
    summary.breadth_scope = BREADTH_SCOPE
    # updated_at 用快照的全量刷新时刻（而非本次请求的 now()），缓存命中多小时后不漂移。
    # snap.updated_at 为 unix epoch，需转成与 compose_summary 同一「北京时间」字符串口径。
    summary.updated_at = datetime.fromtimestamp(snap.updated_at, us_data.BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    # 领涨/领跌只保留实际涨/跌的板块（板块数不足 3 时 compose 的 Top3 切片会混入对手方）
    summary.top_gainers = [s for s in summary.top_gainers if s.change_pct > 0]
    summary.top_losers = [s for s in summary.top_losers if s.change_pct < 0]
    return summary


@router.get("/sectors", response_model=List[UsSector], summary="美股 GICS 板块涨跌榜")
def get_us_sectors():
    """11 个 GICS 板块等权涨跌，按涨跌幅降序（领涨在上）。"""
    snap = get_us_snapshot()
    if not snap:
        raise HTTPException(status_code=503, detail="美股数据获取失败，请稍后重试")
    return snap.sectors


@router.get("/sectors/{name}/constituents", response_model=List[UsConstituent],
            summary="板块成分股")
def get_us_sector_constituents(name: str):
    """板块成分按涨跌幅降序（成分 = 标普500 中该 GICS 板块成员）。"""
    if name not in get_sector_cns():
        raise HTTPException(status_code=404, detail="未知板块")
    snap = get_us_snapshot()
    if not snap:
        raise HTTPException(status_code=503, detail="美股数据获取失败，请稍后重试")
    members = load_us_constituents()
    stocks = us_data.sector_constituents(members, list(snap.quote_map.values()), name)
    return stocks


@router.get("/ai-summary", summary="AI 美股一句话复盘（流式）")
async def get_us_ai_summary():
    """美股复盘一句话主线，SSE 流式输出。

    先推「🤖 AI 正在复盘美股...」开场帧占位，随后流式输出模型文本，
    以 [DONE] 收尾；AI 未配置/调用异常时降级为 ⚠️/❌ 兜底文案。
    """
    from app.services.ai_analyst import analyze_us_market_stream
    from app.services.sse import format_sse_data

    async def event_stream():
        yield format_sse_data("🤖 AI 正在复盘美股...")
        # 快照可能触发首访/跨交易日全量重拉（~60s 阻塞），挪到线程池避免卡住事件循环
        snap = await run_in_threadpool(get_us_snapshot)
        if not snap:
            yield format_sse_data("❌ 美股数据获取失败，请稍后重试")
            yield format_sse_data("[DONE]")
            return
        async for chunk in analyze_us_market_stream(snap):
            yield format_sse_data(chunk)
        yield format_sse_data("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "Connection": "keep-alive",
                                      "X-Accel-Buffering": "no"})
