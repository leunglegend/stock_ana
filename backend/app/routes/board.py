"""
板块相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List

from app.services import board_data
from app.services.data_cache import (
    get_industry_boards_cached,
    get_concept_boards_cached,
    get_market_summary_cached,
)
from app.services.ai_analyst import analyze_market_stream
from app.models.schemas import BoardInfo, BoardStock, MarketSummary

router = APIRouter(prefix="/api/board", tags=["板块"])


@router.get("/industry", response_model=List[BoardInfo], summary="行业板块列表")
async def get_industry_boards():
    """获取行业板块涨跌幅排行（内存缓存，毫秒级响应）"""
    data = get_industry_boards_cached()
    if not data:
        raise HTTPException(status_code=503, detail="行业板块数据获取失败，请稍后重试")
    return data


@router.get("/concept", response_model=List[BoardInfo], summary="概念板块列表")
async def get_concept_boards():
    """获取概念板块涨跌幅排行（内存缓存，毫秒级响应）"""
    data = get_concept_boards_cached()
    if not data:
        raise HTTPException(status_code=503, detail="概念板块数据获取失败，请稍后重试")
    return data


@router.get("/{board_type}/{board_name}/stocks", response_model=List[BoardStock], summary="板块成分股")
async def get_board_stocks(board_type: str, board_name: str):
    """
    获取板块内的股票列表
    - board_type: industry (行业) / concept (概念)
    - board_name: 板块名称
    """
    if board_type not in ["industry", "concept"]:
        raise HTTPException(status_code=400, detail="board_type 必须是 industry 或 concept")

    data = board_data.get_board_stocks(board_name, board_type)
    if not data:
        raise HTTPException(status_code=503, detail="板块成分股获取失败")
    return data


@router.get("/market/summary", response_model=MarketSummary, summary="市场概览")
async def get_market_summary():
    """获取大盘指数、涨跌家数等市场概况（内存缓存，毫秒级响应）"""
    data = get_market_summary_cached()
    if not data:
        raise HTTPException(status_code=503, detail="市场数据获取失败")
    return data


@router.get("/market/ai-summary", summary="AI 市场点评（流式）")
async def get_market_ai_summary():
    """
    AI 一句话点评当日市场，SSE 流式返回
    """
    async def event_stream():
        yield "data: 🤖 AI 正在分析市场数据...\n\n"

        # 获取市场数据
        summary = get_market_summary_cached()
        boards = get_industry_boards_cached()

        if not summary:
            yield "data: ❌ 市场数据获取失败，请稍后重试\n\n"
            yield "data: [DONE]\n\n"
            return

        async for chunk in analyze_market_stream(summary, boards or []):
            yield f"data: {chunk}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
