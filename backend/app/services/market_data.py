"""
市场概览数据服务 - 大盘指数、涨跌家数等
主力数据源：新浪（稳定）+ 东方财富（涨跌统计）
"""
import time
import math
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.models.schemas import MarketSummary
from app.services.stock_data import _get_ak, _retry


# 缓存
_summary_cache = {
    "data": None,
    "time": None,
    "fetched_at": None,
    "degraded": False,
}
_CACHE_TTL = 120  # 缓存2分钟
_summary_last_degraded = False


def get_market_summary() -> Optional[MarketSummary]:
    """获取市场概览数据（带缓存）"""
    result, _, _ = get_market_summary_with_meta()
    return result


def get_market_summary_with_meta() -> tuple[Optional[MarketSummary], bool, datetime | None]:
    """获取市场概览、过期/降级标记和真实抓取时间。"""
    now = time.time()
    cache = _summary_cache
    cache_data = cache.get("data")
    cache_time = cache.get("time")
    if cache_data and cache_time and (now - cache_time) < _CACHE_TTL:
        fetched_at = cache.get("fetched_at") or datetime.fromtimestamp(cache_time, tz=timezone.utc)
        return cache_data, True, fetched_at

    result = _fetch_market_summary()
    degraded = _summary_last_degraded
    fetched_at = datetime.now(timezone.utc) if result else None
    if result:
        cache["data"] = result
        cache["time"] = now
        cache["fetched_at"] = fetched_at
        cache["degraded"] = degraded
    return result, degraded if result else True, fetched_at


@_retry(max_retries=3, delay=2)
def _fetch_index_spot_sina(ak):
    """新浪-指数实时行情（全量，562个指数）"""
    return ak.stock_zh_index_spot_sina()


@_retry(max_retries=2, delay=2)
def _fetch_spot_em(ak):
    """东方财富-A股实时行情（全量，用于涨跌统计）"""
    return ak.stock_zh_a_spot_em()


@_retry(max_retries=2, delay=3)
def _fetch_zt_pool_em(ak):
    """东方财富-涨停池"""
    return ak.stock_zt_pool_em(date=time.strftime("%Y%m%d"))


@_retry(max_retries=2, delay=3)
def _fetch_dt_pool_em(ak):
    """东方财富-跌停池（跌停股池，dtgc=跌停股池）"""
    return ak.stock_zt_pool_dtgc_em(date=time.strftime("%Y%m%d"))


def _fetch_market_summary() -> Optional[MarketSummary]:
    """获取市场概览数据"""
    global _summary_last_degraded
    _summary_last_degraded = False
    ak = _get_ak()
    result = MarketSummary()
    errors = []

    # 1. 三大指数（新浪实时，主力数据源）
    try:
        df = _fetch_index_spot_sina(ak)
        if df is None or df.empty:
            raise RuntimeError("指数行情为空")

        # 查找上证指数
        missing_indices = []
        row = df[df["代码"] == "sh000001"]
        if not row.empty:
            r = row.iloc[0]
            result.sh_index = round(float(r.get("最新价", 0) or 0), 2)
            result.sh_change_pct = round(float(r.get("涨跌幅", 0) or 0), 2)
            result.sh_change_amount = round(float(r.get("涨跌额", 0) or 0), 2)
        else:
            missing_indices.append("上证")

        # 深证成指
        row = df[df["代码"] == "sz399001"]
        if not row.empty:
            r = row.iloc[0]
            result.sz_index = round(float(r.get("最新价", 0) or 0), 2)
            result.sz_change_pct = round(float(r.get("涨跌幅", 0) or 0), 2)
            result.sz_change_amount = round(float(r.get("涨跌额", 0) or 0), 2)
        else:
            missing_indices.append("深证")

        # 创业板指
        row = df[df["代码"] == "sz399006"]
        if not row.empty:
            r = row.iloc[0]
            result.cyb_index = round(float(r.get("最新价", 0) or 0), 2)
            result.cyb_change_pct = round(float(r.get("涨跌幅", 0) or 0), 2)
            result.cyb_change_amount = round(float(r.get("涨跌额", 0) or 0), 2)
        else:
            missing_indices.append("创业板")
        if missing_indices:
            errors.append(f"指数缺失:{','.join(missing_indices)}")
    except Exception as e:
        errors.append(f"指数:{e}")

    # 2. 涨跌家数统计 + 成交额（从全量实时行情统计）
    try:
        rise, fall, flat, total_amount, stats_degraded = _fetch_market_stats(ak)
        result.rise_count = rise
        result.fall_count = fall
        result.flat_count = flat
        result.total_amount = round(total_amount / 100000000, 2)  # 元转亿
        if stats_degraded:
            errors.append("涨跌统计:使用降级估算")
    except Exception as e:
        errors.append(f"涨跌统计:{e}")

    # 3. 涨跌停数量
    try:
        limit_up, limit_down, limits_degraded = _fetch_limit_stats(ak)
        result.limit_up_count = limit_up
        result.limit_down_count = limit_down
        if limits_degraded:
            errors.append("涨跌停统计:部分数据不可用")
    except Exception as e:
        errors.append(f"涨跌停统计:{e}")

    if errors:
        _summary_last_degraded = True
        print(f"市场概览部分数据获取失败: {'; '.join(errors)}")

    return result


def _fetch_market_stats(ak) -> Tuple[int, int, int, float, bool]:
    """统计市场涨跌家数、总成交额
    优先从全量实时行情统计；失败则用行业板块数据估算
    返回: (上涨, 下跌, 平盘, 总成交额(元), 是否降级)
    """
    # 方案1：全量个股实时行情（最准确）
    try:
        df = _fetch_spot_em(ak)
        if df is not None and not df.empty:
            rise, fall, flat, total = _calc_stats_from_spot(df)
            if rise + fall + flat > 0:
                amount_available = any(col in df.columns for col in ("成交额", "总金额"))
                return rise, fall, flat, total, not amount_available
    except Exception as e:
        print(f"全量行情统计失败: {e}，尝试用板块数据估算...")

    # 方案2：用行业板块数据估算（fallback）
    try:
        rise, fall, amount = _estimate_stats_from_boards(ak)
        return rise, fall, 0, amount, True
    except Exception as e:
        print(f"板块估算也失败: {e}")
        return 0, 0, 0, 0.0, True


def _calc_stats_from_spot(df) -> Tuple[int, int, int, float]:
    """从全量个股行情数据计算涨跌家数和成交额"""
    # 查找涨跌幅列（兼容不同列名）
    pct_col = None
    for col in ["涨跌幅", "涨跌幅(%)", "涨幅"]:
        if col in df.columns:
            pct_col = col
            break

    # 查找成交额列
    amount_col = None
    for col in ["成交额", "总金额"]:
        if col in df.columns:
            amount_col = col
            break

    if pct_col is None:
        return 0, 0, 0, 0.0

    rise = 0
    fall = 0
    flat = 0

    for _, row in df.iterrows():
        pct = row.get(pct_col, 0)
        try:
            pct_val = float(pct)
            if math.isnan(pct_val):
                continue
        except (ValueError, TypeError):
            continue

        if pct_val > 0:
            rise += 1
        elif pct_val < 0:
            fall += 1
        else:
            flat += 1

    total_amount = 0.0
    if amount_col:
        try:
            total_amount = float(df[amount_col].sum())
        except Exception:
            total_amount = 0.0

    return rise, fall, flat, total_amount


def _estimate_stats_from_boards(ak) -> Tuple[int, int, float]:
    """从行业板块数据估算涨跌家数和成交额（fallback 方案）"""
    from app.services.board_data import _fetch_board_industry_summary_ths, _parse_board_ths_summary

    df = _fetch_board_industry_summary_ths(ak)
    boards = _parse_board_ths_summary(df)

    rise = sum(b.rise_count for b in boards)
    fall = sum(b.fall_count for b in boards)
    # 同花顺板块总成交额单位是亿，转回元
    total_amount = sum(b.total_turnover for b in boards) * 100000000

    return rise, fall, total_amount


def _fetch_limit_stats(ak) -> Tuple[int, int, bool]:
    """统计涨跌停数量
    返回: (涨停数, 跌停数, 是否降级)
    """
    limit_up = 0
    limit_down = 0
    degraded = False

    # 涨停池
    try:
        df = _fetch_zt_pool_em(ak)
        if df is not None and not df.empty:
            limit_up = len(df)
    except Exception as e:
        degraded = True
        print(f"获取涨停池失败: {e}")

    # 跌停池
    try:
        df = _fetch_dt_pool_em(ak)
        if df is not None and not df.empty:
            limit_down = len(df)
    except Exception as e:
        degraded = True
        print(f"获取跌停池失败: {e}")

    return limit_up, limit_down, degraded
