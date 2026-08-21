"""
AI 分析服务 - 基于火山引擎 Coding Plan (Claude API 兼容)
"""
import os
from typing import AsyncGenerator, Optional

from app.config import settings
from app.models.schemas import StockInfo, KLineData, FinancialData


SYSTEM_PROMPT = """你是一位资深的证券分析师，擅长A股市场的基本面分析和技术面分析。
请根据提供的股票数据，给出专业、客观、有深度的投资分析报告。

要求：
1. 分析要全面，涵盖公司基本面、财务状况、技术走势、估值水平等维度
2. 语言要专业但通俗易懂，适合普通投资者阅读
3. 投资建议要明确（买入/持有/观望/卖出），并给出充分的理由
4. 必须包含风险提示
5. 不要编造数据，所有分析基于提供的数据
6. 使用中文回答
7. 字数控制在800-1200字左右

输出格式：
## 一、公司概况
## 二、财务健康度分析
## 三、技术面分析
## 四、估值水平评估
## 五、投资建议
## 六、风险提示

⚠️ 重要提示：你的分析仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。
"""


def _build_user_prompt(
    stock_info: StockInfo,
    kline_data: KLineData,
    financial: FinancialData
) -> str:
    """构建用户提示词"""
    kline_list = kline_data.kline if kline_data else []
    recent_kline = []
    for item in kline_list[-30:]:
        recent_kline.append(
            f"{item.date}: 开{item.open} 高{item.high} 低{item.low} 收{item.close} 量{item.volume}"
        )

    # 价格变动统计
    if len(kline_list) >= 20:
        price_20d_ago = kline_list[-20].close
        price_5d_ago = kline_list[-5].close
        current_price = kline_list[-1].close
        change_5d = (current_price - price_5d_ago) / price_5d_ago * 100 if price_5d_ago else 0
        change_20d = (current_price - price_20d_ago) / price_20d_ago * 100 if price_20d_ago else 0
    else:
        change_5d = change_20d = 0
        current_price = stock_info.price if stock_info else 0

    # 年内最高最低
    if kline_list:
        year_high = max(item.high for item in kline_list)
        year_low = min(item.low for item in kline_list)
        from_high_pct = (current_price - year_high) / year_high * 100 if year_high else 0
        from_low_pct = (current_price - year_low) / year_low * 100 if year_low else 0
    else:
        year_high = year_low = from_high_pct = from_low_pct = 0

    pe_str = f"{financial.pe:.2f}倍" if financial.pe else "暂无数据"
    pb_str = f"{financial.pb:.2f}倍" if financial.pb else "暂无数据"
    mv_str = f"{financial.total_mv:.2f}亿元" if financial.total_mv else "暂无数据"
    roe_str = f"{financial.roe}%" if financial.roe else "暂无数据"
    np_str = f"{financial.net_profit}亿元" if financial.net_profit else "暂无数据"
    rev_str = f"{financial.revenue}亿元" if financial.revenue else "暂无数据"
    gm_str = f"{financial.gross_margin}%" if financial.gross_margin else "暂无数据"
    nm_str = f"{financial.net_margin}%" if financial.net_margin else "暂无数据"

    prompt = f"""
请分析以下A股股票并给出投资建议：

【股票基本信息】
- 股票代码：{stock_info.code}
- 股票名称：{stock_info.name}
- 当前价格：{stock_info.price} 元
- 今日涨跌幅：{stock_info.change_pct}%
- 今日涨跌额：{stock_info.change_amount} 元
- 今开：{stock_info.open} 元
- 昨收：{stock_info.pre_close} 元
- 最高：{stock_info.high} 元
- 最低：{stock_info.low} 元
- 成交量：{stock_info.volume} 手
- 成交额：{stock_info.amount} 元

【近期走势】
- 近5日涨跌幅：{change_5d:.2f}%
- 近20日涨跌幅：{change_20d:.2f}%
- 近一年最高：{year_high:.2f} 元（距高点 {from_high_pct:.2f}%）
- 近一年最低：{year_low:.2f} 元（距低点 {from_low_pct:.2f}%）

【最近30个交易日K线数据】
{chr(10).join(recent_kline)}

【主要财务指标】
- 市盈率（PE）：{pe_str}
- 市净率（PB）：{pb_str}
- 总市值：{mv_str}
- 净资产收益率（ROE）：{roe_str}
- 净利润：{np_str}
- 营业收入：{rev_str}
- 毛利率：{gm_str}
- 净利率：{nm_str}
- 报告期：{financial.report_date if financial.report_date else '暂无数据'}

请基于以上数据，按照要求的格式进行全面分析并给出投资建议。
"""
    return prompt


def _get_client():
    """获取 Anthropic 客户端（通过火山引擎 Coding Plan）"""
    from anthropic import AsyncAnthropic

    base_url = settings.ARK_BASE_URL
    api_key = settings.ARK_API_KEY

    return AsyncAnthropic(
        base_url=base_url,
        api_key=api_key,
    )


async def analyze_stock_stream(
    stock_info: StockInfo,
    kline_data: KLineData,
    financial: FinancialData
) -> AsyncGenerator[str, None]:
    """
    流式分析股票，逐步返回分析结果
    """
    if not settings.ai_available:
        yield "⚠️ AI 分析服务暂不可用：未配置 API Key 和模型。\n\n"
        yield "请设置环境变量 ARK_API_KEY 和 ARK_MODEL。"
        return

    try:
        client = _get_client()
        user_prompt = _build_user_prompt(stock_info, kline_data, financial)

        async with client.messages.stream(
            model=settings.ARK_MODEL,
            max_tokens=2000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"\n\n❌ AI 分析出错：{str(e)}"
        print(f"AI 分析错误: {e}")


async def analyze_stock(
    stock_info: StockInfo,
    kline_data: KLineData,
    financial: FinancialData
) -> Optional[str]:
    """
    非流式分析（一次性返回全部结果）
    """
    if not settings.ai_available:
        return "⚠️ AI 分析服务暂不可用：未配置 API Key 和模型。"

    try:
        client = _get_client()
        user_prompt = _build_user_prompt(stock_info, kline_data, financial)

        message = await client.messages.create(
            model=settings.ARK_MODEL,
            max_tokens=2000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        return message.content[0].text
    except Exception as e:
        print(f"AI 分析错误: {e}")
        return f"AI 分析出错：{str(e)}"


# ===== 市场点评 =====

MARKET_SUMMARY_SYSTEM_PROMPT = """你是一位资深的A股市场评论员，擅长用简洁专业的语言解读当日市场行情。

要求：
1. 用一段话总结当日市场整体表现，150-200字左右
2. 结合指数表现、涨跌家数、板块特征进行分析
3. 语言专业但通俗易懂，适合普通投资者阅读
4. 不要编造数据，所有分析基于提供的数据
5. 使用中文回答
6. 末尾必须加上风险提示：「市场有风险，投资需谨慎。」

风格：客观、理性、有洞察力，不做预测，只做解读。
"""


def _build_market_summary_prompt(
    sh_index, sh_change_pct, sh_change_amount,
    sz_index, sz_change_pct, sz_change_amount,
    cyb_index, cyb_change_pct, cyb_change_amount,
    rise_count, fall_count, limit_up, limit_down, total_amount,
    top_boards, bottom_boards
) -> str:
    """构建市场点评 prompt"""

    def fmt_idx(name, val, pct, amt):
        if val is None:
            return f"- {name}：暂无数据"
        sign = '+' if pct and pct > 0 else ''
        amt_sign = '+' if amt and amt > 0 else ''
        amt_str = f'{amt_sign}{amt:.2f}点' if amt else ''
        return f"- {name}：{val:.2f}点 {sign}{pct:.2f}% {amt_str}".strip()

    boards_top_str = '\n'.join([f"  {b.name}（{b.change_pct:+.2f}%）" for b in top_boards[:5]]) if top_boards else "  暂无数据"
    boards_bottom_str = '\n'.join([f"  {b.name}（{b.change_pct:+.2f}%）" for b in bottom_boards[:5]]) if bottom_boards else "  暂无数据"

    prompt = f"""
请根据以下A股市场数据，给出一段专业的市场点评：

【三大指数】
{fmt_idx('上证指数', sh_index, sh_change_pct, sh_change_amount)}
{fmt_idx('深证成指', sz_index, sz_change_pct, sz_change_amount)}
{fmt_idx('创业板指', cyb_index, cyb_change_pct, cyb_change_amount)}

【市场情绪】
- 上涨家数：{rise_count} 家
- 下跌家数：{fall_count} 家
- 涨停：{limit_up} 家
- 跌停：{limit_down} 家
- 两市成交额：{total_amount:.0f} 亿元

【涨幅居前板块】
{boards_top_str}

【跌幅居前板块】
{boards_bottom_str}

请用一段话进行点评，150-200字左右。
"""
    return prompt


async def analyze_market_stream(summary_data, boards_data) -> AsyncGenerator[str, None]:
    """
    流式生成市场点评
    :param summary_data: MarketSummary 对象
    :param boards_data: 板块列表（BoardInfo 数组）
    """
    if not settings.ai_available:
        yield "⚠️ AI 服务暂不可用：未配置 API Key。"
        return

    try:
        # 取涨幅前5和跌幅前5的板块
        top_boards = sorted(boards_data, key=lambda x: x.change_pct, reverse=True)[:5] if boards_data else []
        bottom_boards = sorted(boards_data, key=lambda x: x.change_pct)[:5] if boards_data else []

        user_prompt = _build_market_summary_prompt(
            sh_index=summary_data.sh_index,
            sh_change_pct=summary_data.sh_change_pct,
            sh_change_amount=summary_data.sh_change_amount,
            sz_index=summary_data.sz_index,
            sz_change_pct=summary_data.sz_change_pct,
            sz_change_amount=summary_data.sz_change_amount,
            cyb_index=summary_data.cyb_index,
            cyb_change_pct=summary_data.cyb_change_pct,
            cyb_change_amount=summary_data.cyb_change_amount,
            rise_count=summary_data.rise_count,
            fall_count=summary_data.fall_count,
            limit_up=summary_data.limit_up_count,
            limit_down=summary_data.limit_down_count,
            total_amount=summary_data.total_amount,
            top_boards=top_boards,
            bottom_boards=bottom_boards,
        )

        client = _get_client()
        async with client.messages.stream(
            model=settings.ARK_MODEL,
            max_tokens=500,
            temperature=0.7,
            system=MARKET_SUMMARY_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"\n\n❌ AI 点评出错：{str(e)}"
        print(f"AI 市场点评错误: {e}")
