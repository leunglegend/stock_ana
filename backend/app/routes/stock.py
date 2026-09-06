"""
股票相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from typing import List

from datetime import datetime, timezone

from app.services import stock_data
from app.services.ai_analyst import analyze_stock_stream, generate_decision_report
from app.services.signal_rules import analyze_signals
from app.services.sse import format_sse_data
from app.models.schemas import (
    StockInfo, KLineData, FinancialData, StockSearchItem, StockDecisionReport
)

router = APIRouter(prefix="/api/stock", tags=["股票"])


@router.get("/search", response_model=List[StockSearchItem], summary="搜索股票")
async def search_stock(q: str):
    """根据关键词搜索股票（代码或名称）"""
    results = await run_in_threadpool(stock_data.search_stock, q)
    return results


@router.get("/{code}", response_model=StockInfo, summary="获取股票实时行情")
async def get_stock(code: str):
    """获取股票基本信息和实时行情（实时接口失败时用K线数据降级）"""
    info = await run_in_threadpool(stock_data.get_stock_info, code)
    if not info:
        # 降级：用同一份 K 线缓存中的最新数据构造，避免重复上游请求
        kline = await run_in_threadpool(stock_data.get_kline_data, code, "daily", 10)
        if kline and kline.kline:
            last = kline.kline[-1]
            prev = kline.kline[-2] if len(kline.kline) > 1 else last
            change = last.close - prev.close
            change_pct = (change / prev.close * 100) if prev.close else 0
            info = StockInfo(
                code=kline.code,
                name=kline.name,
                price=last.close,
                change_pct=round(change_pct, 2),
                change_amount=round(change, 2),
                open=last.open,
                pre_close=prev.close,
                high=last.high,
                low=last.low,
                volume=last.volume,
                amount=0,
            )
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票代码: {code}")
    return info


@router.get("/{code}/kline", response_model=KLineData, summary="获取K线数据")
async def get_kline(code: str, period: str = "daily", days: int = 250):
    """
    获取K线数据
    - period: daily(日K), weekly(周K), monthly(月K)
    - days: 获取天数
    """
    kline = await run_in_threadpool(stock_data.get_kline_data, code, period, days)
    if not kline:
        raise HTTPException(status_code=404, detail=f"获取K线数据失败: {code}")
    return kline


@router.get("/{code}/financial", response_model=FinancialData, summary="获取财务数据")
async def get_financial(code: str):
    """获取股票财务指标"""
    financial = await run_in_threadpool(stock_data.get_financial_data, code)
    if not financial:
        raise HTTPException(status_code=404, detail=f"获取财务数据失败: {code}")
    return financial


@router.get("/{code}/decision-report", response_model=StockDecisionReport, summary="生成个股 AI 决策报告")
async def get_decision_report(code: str):
    """基于当前行情、日 K 线、财务和确定性信号生成临时决策报告。"""
    info = await run_in_threadpool(stock_data.get_stock_info, code)
    kline = await run_in_threadpool(stock_data.get_kline_data, code, "daily", 250)
    if not info and kline and kline.kline:
        last = kline.kline[-1]
        prev = kline.kline[-2] if len(kline.kline) > 1 else last
        change = last.close - prev.close
        info = StockInfo(
            code=kline.code, name=kline.name, price=last.close,
            change_pct=round(change / prev.close * 100, 2) if prev.close else 0,
            change_amount=round(change, 2), open=last.open, pre_close=prev.close,
            high=last.high, low=last.low, volume=last.volume, amount=0,
        )
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票代码: {code}")
    if not kline or not kline.kline:
        raise HTTPException(status_code=502, detail=f"获取 K 线数据失败: {code}")

    financial = await run_in_threadpool(stock_data.get_financial_data, code)
    signal_analysis = analyze_signals(kline.kline, None)
    signals = [signal.model_dump() for signal in signal_analysis.signals]
    try:
        result = await generate_decision_report(info, kline, financial, signals)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result.update({
        "code": info.code,
        "name": info.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of": signal_analysis.as_of,
        "signals": signals,
        "data_quality": {
            "level": "limited" if not financial else "usable",
            "warnings": ["当前未接入新闻、公告、资金流和盈利预期数据"],
            "technical_as_of": signal_analysis.as_of,
        },
    })
    return result


async def analyze_stock(code: str):
    """
    AI 分析股票，SSE 流式返回分析结果
    使用 GET 方便前端 EventSource 直接调用
    """
    async def event_stream():
        # 第一步：获取股票数据
        yield format_sse_data("📊 正在获取股票数据...")

        info = await run_in_threadpool(stock_data.get_stock_info, code)

        # 获取K线数据
        kline = await run_in_threadpool(stock_data.get_kline_data, code, "daily", 250)

        # 如果实时行情失败但K线数据可用，用K线最新数据构造基本信息
        if not info and kline and kline.kline:
            from app.models.schemas import StockInfo
            last = kline.kline[-1]
            prev = kline.kline[-2] if len(kline.kline) > 1 else last
            change = last.close - prev.close
            change_pct = (change / prev.close * 100) if prev.close else 0
            info = StockInfo(
                code=kline.code,
                name=kline.name,
                price=last.close,
                change_pct=round(change_pct, 2),
                change_amount=round(change, 2),
                open=last.open,
                pre_close=prev.close,
                high=last.high,
                low=last.low,
                volume=last.volume,
                amount=0,
            )

        if not info:
            yield format_sse_data("❌ 未找到该股票，请检查代码是否正确")
            yield format_sse_data("[DONE]")
            return

        financial = await run_in_threadpool(stock_data.get_financial_data, code)

        yield format_sse_data("🤖 AI 正在分析中，请稍候...")

        # 第二步：流式输出 AI 分析结果
        async for chunk in analyze_stock_stream(info, kline, financial):
            yield format_sse_data(chunk)

        yield format_sse_data("[DONE]")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
