"""
AI 分析服务 - 基于火山引擎 Coding Plan (Claude API 兼容)
"""
import json
import os
from typing import AsyncGenerator, Optional, List, Tuple

from app.config import settings
from app.models.schemas import StockInfo, KLineData, FinancialData


DECISION_REPORT_SYSTEM_PROMPT = """你是严谨的A股决策分析师。仅依据用户提供的行情、日K线、财务指标和确定性技术信号生成结构化决策报告。
必须只返回一个严格 JSON 对象，不要 Markdown 代码围栏，不要额外文字。不得编造新闻、情绪、公告、资金流、盈利预期或最新动态；这些字段没有输入时必须返回 null 或明确的 unavailable 状态。关键价位只能从给定 K 线推导，无法可靠推导则返回 null。结论必须包含风险、失效条件和数据限制。报告仅供参考，不构成投资建议。

JSON 字段：
{
  "conclusion": {"action":"buy|hold|sell", "label":"强烈买入|买入|观望|减仓|卖出", "score":0, "rationale":""},
  "trend": {"label":"", "phase":"", "summary":""},
  "levels": {"support":null, "resistance":null, "entry_low":null, "entry_high":null, "stop_loss":null, "target_price":null},
  "risks": [], "catalysts": [],
  "sentiment": {"status":"unavailable", "summary":"当前未接入新闻/情绪数据"},
  "fundamentals": {"summary":""},
  "latest_developments": {"status":"unavailable", "summary":"当前未接入公告与最新动态数据"},
  "checklist": [],
  "analysis_markdown":""
}
"""
SYSTEM_PROMPT = """你是一位资深的证券分析师，擅长A股市场的基本面分析和技术面分析。
请根据提供的股票数据，给出专业、客观、有深度的投资分析报告。

要求：
1. 分析要全面，涵盖公司基本面、财务状况、技术走势、估值水平等维度
2. 语言要专业但通俗易懂，适合普通投资者阅读
3. 投资建议要明确，并给出充分的理由
4. 必须包含风险提示
5. 不要编造数据，所有分析基于提供的数据
6. 使用中文回答

## 输出格式要求（严格遵守）

先输出一个 JSON 代码块（评分数据），然后再输出 Markdown 详细分析。

### 第一部分：评分 JSON（放在 ```json 代码块中）

JSON 结构：
{
  "score": 综合评分0-100的整数,
  "rating": "强烈买入" | "买入" | "观望" | "减仓" | "卖出",
  "dimensions": {
    "technical": 技术面评分0-100,
    "fundamental": 基本面评分0-100,
    "sentiment": 情绪面评分0-100,
    "risk": 风险度评分0-100（分数越高风险越低）
  },
  "key_points": ["核心要点1", "核心要点2", "核心要点3"],
  "action_advice": "一句话操作建议"
}

评分标准：
- 80-100：强烈买入 — 高胜率机会，多维度共振向好
- 60-79：买入 — 偏积极，主要维度向好，少量存疑
- 40-59：观望 — 信号分歧或确认不足，等待触发条件
- 20-39：减仓 — 风险明显抬升，优先降低暴露
- 0-19：卖出 — 趋势或风险显著恶化，优先退出

### 第二部分：详细分析（Markdown 格式）

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
    """获取异步 Anthropic 客户端（通过火山引擎 Coding Plan）"""
    from anthropic import AsyncAnthropic

    base_url = settings.ARK_BASE_URL
    api_key = settings.ARK_API_KEY

    return AsyncAnthropic(
        base_url=base_url,
        api_key=api_key,
    )


def _get_sync_client():
    """获取同步 Anthropic 客户端（通过火山引擎 Coding Plan）"""
    from anthropic import Anthropic

    base_url = settings.ARK_BASE_URL
    api_key = settings.ARK_API_KEY

    return Anthropic(
        base_url=base_url,
        api_key=api_key,
    )


async def generate_decision_report(
    stock_info: StockInfo,
    kline_data: KLineData,
    financial: FinancialData,
    signals: list[dict],
) -> dict:
    """生成并规范化结构化个股决策报告。"""
    if not settings.ai_available:
        raise RuntimeError("AI 决策报告服务暂不可用：未配置 API Key 和模型")

    prompt = _build_decision_report_prompt(stock_info, kline_data, financial, signals)
    try:
        client = _get_client()
        message = await client.messages.create(
            model=settings.ARK_MODEL,
            # 决策报告为结构化 JSON 输出，无需深度思考。显式关闭 thinking：
            # DeepSeek 等推理模型默认会把 max_tokens 全部消耗在思考块上，导致
            # TextBlock 为空、最终解析失败（stop_reason=max_tokens）。
            thinking={"type": "disabled"},
            max_tokens=4000,
            system=DECISION_REPORT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(getattr(block, "text", "") or "" for block in message.content)
        data = _extract_json(text)
        if not isinstance(data, dict):
            # 部分模型会先把完整答案写在 thinking 块中而 TextBlock 为空，兜底解析 thinking
            thinking = "".join(getattr(block, "thinking", "") or "" for block in message.content)
            data = _extract_json(thinking) if thinking else None
        if not isinstance(data, dict):
            raise ValueError("AI 返回的决策报告不是有效 JSON")
        return _normalize_decision_report(data)
    except Exception as exc:
        print(f"AI 决策报告错误: {exc}")
        raise RuntimeError(f"AI 决策报告生成失败：{exc}") from exc


def _build_decision_report_prompt(stock_info, kline_data, financial, signals) -> str:
    rows = kline_data.kline if kline_data else []
    recent = [
        {"date": row.date, "open": row.open, "high": row.high, "low": row.low,
         "close": row.close, "ma5": row.ma5, "ma10": row.ma10, "ma20": row.ma20,
         "dif": row.dif, "dea": row.dea, "rsi6": row.rsi6}
        for row in rows[-60:]
    ]
    return json.dumps({
        "stock": stock_info.model_dump(),
        "financial": financial.model_dump() if financial else {},
        "technical_signals": signals,
        "daily_bars": recent,
        "constraints": [
            "仅使用以上数据；新闻、情绪、公告、资金流和盈利预期均未提供",
            "无法由数据支持的字段必须为 null 或 unavailable",
            "关键价位必须说明是基于历史 K 线的估算，不得伪造精确预测",
        ],
    }, ensure_ascii=False, indent=2)


def _normalize_decision_report(data: dict) -> dict:
    conclusion = data.get("conclusion") if isinstance(data.get("conclusion"), dict) else {}
    score = _bounded_int(conclusion.get("score"), 0)
    label = str(conclusion.get("label") or "观望")
    action = str(conclusion.get("action") or "hold").lower()
    if action not in {"buy", "hold", "sell"}:
        action = _action_from_label(label)
    if action == "hold" and label in {"强烈买入", "买入", "减仓", "卖出"}:
        action = _action_from_label(label)
    return {
        "conclusion": {"action": action, "label": label, "score": score,
                       "rationale": _text(conclusion.get("rationale"))},
        "trend": _dict(data.get("trend")),
        "levels": _dict(data.get("levels")),
        "risks": _texts(data.get("risks")),
        "catalysts": _texts(data.get("catalysts")),
        "sentiment": _dict(data.get("sentiment"), {"status": "unavailable", "summary": "当前未接入新闻/情绪数据"}),
        "fundamentals": _dict(data.get("fundamentals")),
        "latest_developments": _dict(data.get("latest_developments"), {"status": "unavailable", "summary": "当前未接入公告与最新动态数据"}),
        "checklist": _texts(data.get("checklist")),
        "analysis_markdown": _text(data.get("analysis_markdown")),
    }


def _action_from_label(label: str) -> str:
    if label in {"强烈买入", "买入"}:
        return "buy"
    if label in {"减仓", "卖出"}:
        return "sell"
    return "hold"


def _bounded_int(value, default: int) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return default


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _texts(value) -> list[str]:
    return [item.strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def _dict(value, default=None) -> dict:
    return dict(value) if isinstance(value, dict) else dict(default or {})

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
- 两市成交额：{_format_market_turnover(total_amount)}

【涨幅居前板块】
{boards_top_str}

【跌幅居前板块】
{boards_bottom_str}

请用一段话进行点评，150-200字左右。
"""
    return prompt


def _format_market_turnover(total_amount: float) -> str:
    amount = float(total_amount or 0)
    return (
        f"{amount:,.0f} 亿元（约 {amount / 10000:.2f} 万亿元），"
        f"不得写成 {amount:,.0f} 万亿元"
    )


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


# ===== 盘后复盘 AI 分析 =====

STOCK_DAILY_ANALYSIS_SYSTEM_PROMPT = """你是一位专业的盘后股票分析师，擅长对当日个股表现做精准复盘。

要求：
1. 聚焦当日表现，结合近期走势给出技术面判断
2. 明确指出关键支撑位和压力位
3. 给出明确的短期观察点和操作建议
4. 必须包含风险提示
5. 语言精炼专业，适合盘后快速阅读
6. 使用中文回答
7. analysis_text 控制在 300-500 字左右，使用 Markdown 格式
8. summary 为一句话摘要，50 字以内

评分标准：
- 80-100：强烈买入 — 高胜率机会，多维度共振向好
- 60-79：买入 — 偏积极，主要维度向好
- 40-59：观望 — 信号分歧或确认不足
- 20-39：减仓 — 风险明显抬升
- 0-19：卖出 — 趋势或风险显著恶化

输出必须是严格的 JSON 格式，包含以下字段：
{
    "score": 0-100整数评分,
    "rating": "强烈买入|买入|观望|减仓|卖出",
    "analysis_text": "详细分析内容...",
    "summary": "一句话摘要"
}

⚠️ 重要提示：你的分析仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。
"""


def _build_stock_daily_prompt(
    stock_code: str,
    stock_name: str,
    quote: StockInfo,
    kline: Optional[KLineData],
) -> str:
    """构建盘后个股分析 prompt。"""
    # 当日行情
    quote_lines = [
        f"股票代码：{stock_code}",
        f"股票名称：{stock_name}",
        f"收盘价：{quote.price} 元",
        f"涨跌幅：{quote.change_pct}%",
        f"涨跌额：{quote.change_amount} 元",
        f"今开：{quote.open} 元",
        f"昨收：{quote.pre_close} 元",
        f"最高：{quote.high} 元",
        f"最低：{quote.low} 元",
        f"成交量：{quote.volume} 手",
        f"成交额：{quote.amount} 元",
    ]

    # K 线数据
    kline_str = "暂无K线数据"
    if kline and kline.kline:
        recent = []
        for item in kline.kline[-30:]:
            recent.append(
                f"{item.date}: 开{item.open} 高{item.high} 低{item.low} 收{item.close} 量{item.volume}"
            )
        kline_str = "\n".join(recent)

    prompt = f"""
请对以下股票进行盘后分析：

【当日行情】
{chr(10).join(quote_lines)}

【近30个交易日K线】
{kline_str}

请按要求进行盘后复盘分析，并以 JSON 格式返回结果。
"""
    return prompt


def _extract_json(text: str) -> Optional[dict]:
    """从 AI 返回文本中提取 JSON 对象。

    通过查找最外层的 { 和 } 来定位 JSON 内容，
    兼容 markdown 代码块、前后多余文本等情况。
    """
    if not text:
        return None
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None
    json_str = text[start:end + 1]
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None


def parse_analysis_score(text: str) -> Optional[dict]:
    """
    从 AI 分析文本中提取评分数据。
    返回 {score, rating, dimensions, key_points, action_advice, content}，
    其中 content 是去除了 JSON 代码块后的纯 Markdown 分析内容。
    """
    if not text:
        return None

    import re

    # 先找 ```json ... ``` 代码块
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    score_data = None
    clean_text = text

    if match:
        json_str = match.group(1).strip()
        try:
            score_data = json.loads(json_str)
            # 去除 JSON 代码块，保留纯分析内容
            clean_text = (text[:match.start()] + text[match.end():]).strip()
        except Exception:
            # JSON 解析失败，用 _extract_json 兜底
            score_data = _extract_json(text)
    else:
        # 没有代码块，尝试直接提取
        score_data = _extract_json(text)

    if not score_data:
        return None

    # 校验 score 字段
    score = score_data.get("score")
    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        return None

    return {
        "score": int(score),
        "rating": score_data.get("rating", "观望"),
        "dimensions": score_data.get("dimensions", {}),
        "key_points": score_data.get("key_points", []),
        "action_advice": score_data.get("action_advice", ""),
        "content": clean_text,
    }


def get_rating_info(rating: str) -> dict:
    """根据评级返回颜色和等级信息"""
    mapping = {
        "强烈买入": {"color": "#dc2626", "level": "strong_buy", "bg_color": "#fef2f2"},
        "买入": {"color": "#ef4444", "level": "buy", "bg_color": "#fef2f2"},
        "观望": {"color": "#d97706", "level": "watch", "bg_color": "#fffbeb"},
        "减仓": {"color": "#059669", "level": "reduce", "bg_color": "#ecfdf5"},
        "卖出": {"color": "#10b981", "level": "sell", "bg_color": "#ecfdf5"},
    }
    return mapping.get(rating, mapping["观望"])


def generate_stock_daily_analysis(
    stock_code: str,
    stock_name: str,
    quote: StockInfo,
    kline: Optional[KLineData],
) -> Tuple[str, str]:
    """
    盘后个股分析（同步版本）。

    返回: (analysis_text, summary)
      - analysis_text：300-500 字 Markdown 分析
      - summary：一句话摘要（50 字以内）
    """
    if not settings.ai_available:
        default_text = "⚠️ AI 分析服务暂不可用：未配置 API Key 和模型。"
        return default_text, "AI 服务暂不可用"

    try:
        client = _get_sync_client()
        user_prompt = _build_stock_daily_prompt(stock_code, stock_name, quote, kline)

        message = client.messages.create(
            model=settings.ARK_MODEL,
            max_tokens=1200,
            system=STOCK_DAILY_ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        text = message.content[0].text

        # 尝试解析 JSON
        data = _extract_json(text)
        if data:
            analysis_text = data.get("analysis_text", text)
            summary = data.get("summary", "")
            return analysis_text, summary

        # 解析失败，把全文作为 analysis_text，取首句作为 summary
        summary = text.split("\n")[0][:50] if text else ""
        return text, summary

    except Exception as e:
        logger_text = f"AI 盘后分析出错：{str(e)}"
        print(logger_text)
        raise RuntimeError(logger_text) from e


DAILY_REPORT_OVERVIEW_SYSTEM_PROMPT = """你是一位资深的投资顾问，擅长从用户自选股中提炼每日复盘重点。

要求：
1. 结合市场整体表现和个股情况，给出 200-300 字的市场总评
2. 从自选股中挑选 3-5 只最值得关注的股票作为关注重点
3. 给出 100-200 字的整体风险提示，客观理性
4. 语言专业但通俗易懂，适合普通投资者
5. 使用中文回答

输出必须是严格的 JSON 格式，包含三个字段：
{
    "market_summary": "200-300字市场总评...",
    "highlights": [
        {"stock_code": "600519", "stock_name": "贵州茅台", "reason": "关注理由..."},
        ...
    ],
    "risk_notes": "100-200字整体风险提示..."
}

⚠️ 重要提示：你的分析仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。
"""


def _build_daily_report_overview_prompt(
    stock_results: List[dict],
    market_data,
) -> str:
    """构建日报总览 prompt。"""
    # 市场数据
    market_lines = []
    if market_data:
        def fmt_idx(name, val, pct):
            if val is None:
                return f"- {name}：暂无数据"
            sign = '+' if pct and pct > 0 else ''
            return f"- {name}：{val:.2f}点 {sign}{pct:.2f}%"

        market_lines = [
            fmt_idx('上证指数', market_data.sh_index, market_data.sh_change_pct),
            fmt_idx('深证成指', market_data.sz_index, market_data.sz_change_pct),
            fmt_idx('创业板指', market_data.cyb_index, market_data.cyb_change_pct),
            f"- 上涨家数：{market_data.rise_count} 家",
            f"- 下跌家数：{market_data.fall_count} 家",
            f"- 涨停：{getattr(market_data, 'limit_up_count', 0)} 家",
            f"- 跌停：{getattr(market_data, 'limit_down_count', 0)} 家",
            f"- 两市成交额：{_format_market_turnover(market_data.total_amount)}",
        ]
    else:
        market_lines = ["- 暂无市场数据"]

    # 个股列表
    stock_lines = []
    for s in stock_results:
        sign = '+' if s['change_pct'] > 0 else ''
        stock_lines.append(
            f"- {s['stock_name']}({s['stock_code']}) {sign}{s['change_pct']:.2f}% — {s['summary']}"
        )

    prompt = f"""
请根据以下数据，为用户生成盘后复盘总览：

【市场概览】
{chr(10).join(market_lines)}

【自选股表现】
{chr(10).join(stock_lines)}

请从以上自选股中挑选 3-5 只最值得关注的股票，并生成市场总评和风险提示。
以 JSON 格式返回结果。
"""
    return prompt


def generate_daily_report_overview(
    stock_results: List[dict],
    market_data,
) -> Tuple[str, List[dict], str]:
    """
    生成盘后复盘整体分析（同步版本）。

    返回: (market_summary, highlights, risk_notes)
      - market_summary：200-300 字市场总评
      - highlights：3-5 只重点关注股票 [{stock_code, stock_name, reason}]
      - risk_notes：100-200 字整体风险提示
    """
    if not settings.ai_available:
        default_summary = "⚠️ AI 服务暂不可用，无法生成市场总评。"
        default_highlights = []
        default_risk = "市场有风险，投资需谨慎。"
        return default_summary, default_highlights, default_risk

    try:
        client = _get_sync_client()
        user_prompt = _build_daily_report_overview_prompt(stock_results, market_data)

        message = client.messages.create(
            model=settings.ARK_MODEL,
            max_tokens=1500,
            system=DAILY_REPORT_OVERVIEW_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        text = message.content[0].text

        # 尝试解析 JSON
        data = _extract_json(text)
        if data:
            market_summary = data.get("market_summary", "")
            highlights = data.get("highlights", [])
            risk_notes = data.get("risk_notes", "")
            # 确保 highlights 格式正确
            valid_highlights = []
            for h in highlights:
                if isinstance(h, dict) and "stock_code" in h and "stock_name" in h:
                    valid_highlights.append({
                        "stock_code": h["stock_code"],
                        "stock_name": h["stock_name"],
                        "reason": h.get("reason", ""),
                    })
            return market_summary, valid_highlights, risk_notes

        # 解析失败，返回默认结构
        return text, [], "市场有风险，投资需谨慎。"

    except Exception as e:
        logger_text = f"AI 日报总览出错：{str(e)}"
        print(logger_text)
        raise RuntimeError(logger_text) from e


# ===== 美股一句话复盘 =====

US_MARKET_SYSTEM_PROMPT = """你是一名美股盘后复盘分析师，为中文投资者做"美股收盘复盘一句话"。

硬性规则（违反即不合格）：
1. 只用中文，输出 40-90 字一段话。
2. 只陈述下面数据里的事实，禁止猜测或编造原因；不得使用"由于 / 受…影响 / 因为 / 因此 / 导致 / 表明"等归因、因果表述。
3. 每条强弱判断必须能对照数据中的可核对数字（指数点位与涨跌幅、板块等权涨跌幅、领涨领跌成分 ticker 与其涨跌幅）。
4. 涨跌范围只限于标普500成分等权口径，不得写成全市场结论；数据不足或主线不明时，直接写"今日美股主线暂不明朗"。
5. 结尾必须追加一句："（标普500成分等权口径，非投资建议。）"
"""


def _build_us_market_prompt(snapshot) -> str:
    """把美股快照转成可核对的事实清单。snapshot 为 None/空时给出兜底引导。"""
    if snapshot is None or not getattr(snapshot, "sectors", None):
        return ("请直接输出：今日美股主线暂不明朗。（标普500成分等权口径，非投资建议。）\n"
                "（当前无可用复盘数据，不要编造板块或个股表现。）")
    lines = [f"【数据日期】美东 {snapshot.as_of}（收盘）"]
    for i in snapshot.indices:
        lines.append(f"- 指数 {i.name}：{i.value:.2f} 点 {i.change_pct:+.2f}%")
    # 领涨/领跌只取实际涨/跌的板块（与 /summary 口径一致），避免全绿日把
    # 「领涨板块 X -0.4%」这类自相矛盾的事实行喂给模型
    def _sector_line(s, word):
        return f"{s.name} {s.change_pct:+.2f}%（{word} {s.leading_symbol} {s.leading_change_pct:+.2f}%）"

    gainers = [s for s in snapshot.sectors if s.change_pct > 0][:3]
    losers = [s for s in snapshot.sectors if s.change_pct < 0][-3:][::-1]
    lines.append("【领涨板块】"
                 + ("；".join(_sector_line(s, "领涨") for s in gainers) if gainers else "无"))
    lines.append("【领跌板块】"
                 + ("；".join(_sector_line(s, "领跌") for s in losers) if losers else "无"))
    adv = sum(s.advancers for s in snapshot.sectors)
    dec = sum(s.decliners for s in snapshot.sectors)
    lines.append(f"【成分广度】标普500成分口径：上涨 {adv} / 下跌 {dec}")
    return "\n".join(lines)


async def analyze_us_market_stream(snapshot) -> "AsyncGenerator[str, None]":
    """流式生成美股复盘一句话（SSE 用）。"""
    if not settings.ai_available:
        yield "⚠️ AI 服务暂不可用：未配置 API Key。"
        return
    try:
        user_prompt = _build_us_market_prompt(snapshot)
        client = _get_client()
        async with client.messages.stream(
            model=settings.ARK_MODEL,
            max_tokens=200,
            system=US_MARKET_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"\n\n❌ AI 复盘出错：{str(e)}"
        print(f"AI 美股复盘错误: {e}")
