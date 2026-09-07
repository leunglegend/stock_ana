"""
股票数据服务 - 基于 AKShare
"""
from typing import List, Optional
import datetime
from math import isfinite
import re
import time
import functools
import threading

from app.models.schemas import (
    StockInfo, KLineData, KLineItem, FinancialData, StockSearchItem
)
from app.schemas.monitor import (
    MonitorIndicators,
    MonitorMetrics,
    MonitorQuote,
    MonitorSnapshot,
)

# 延迟导入 AKShare（安装较重，未安装时也能启动应用）
_ak = None
_pd = None


def _get_ak():
    """获取 AKShare 实例，懒加载"""
    global _ak
    if _ak is None:
        try:
            import akshare as ak
            _ak = ak
        except ImportError:
            raise RuntimeError(
                "AKShare 未安装，请运行：pip install akshare\n"
                "安装文档：https://akshare.akfamily.xyz/"
            )
    return _ak


def _get_pd():
    """获取 pandas 实例"""
    global _pd
    if _pd is None:
        import pandas as pd
        _pd = pd
    return _pd


# 缓存股票列表，避免每次搜索都重新加载
_stock_list_cache = None
_cache_time = None
_CACHE_DURATION = 3600  # 缓存1小时
_stock_list_lock = threading.Lock()
_kline_cache = {}
_kline_cache_lock = threading.Lock()
_kline_fetch_locks = {}
_KLINE_CACHE_DURATION = 60
_KLINE_STALE_DURATION = 300
_FINANCIAL_CACHE = {}
_FINANCIAL_CACHE_LOCK = threading.Lock()
_FINANCIAL_CACHE_DURATION = 300


def _retry(max_retries=3, delay=1):
    """重试装饰器，用于处理网络波动"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    # 只有网络相关错误才重试
                    if any(key in err_str for key in [
                        'connection', 'timeout', 'remote', 'reset',
                        'closed', 'refused', 'network', '503', '502'
                    ]):
                        if i < max_retries - 1:
                            time.sleep(delay * (i + 1))
                            continue
                    raise
            raise last_error
        return wrapper
    return decorator


def _fetch_stock_list():
    """获取 A 股股票列表（多源容错）

    海外网络下深交所(www.szse.cn)可能 SSL 失败、东财全A股分页接口较慢但可用。
    依次尝试上交所 + 深交所，若沪深任一缺失则用东财全 A 股兜底补全。
    """
    ak = _get_ak()
    stocks = []
    errors = []

    # 数据源1：上交所主板 A 股
    try:
        sh_df = ak.stock_info_sh_name_code(symbol="主板A股")
        if sh_df is not None and not sh_df.empty:
            for _, row in sh_df.iterrows():
                code = str(row.get("证券代码", "")).strip()
                name = str(row.get("证券简称", "")).strip()
                if code:
                    stocks.append({"code": code, "name": name})
    except Exception as e:
        errors.append(f"上交所:{e}")

    # 数据源2：深交所 A 股
    try:
        sz_df = ak.stock_info_sz_name_code(symbol="A股列表")
        if sz_df is not None and not sz_df.empty:
            for _, row in sz_df.iterrows():
                code = str(row.get("A股代码", "")).strip()
                name = str(row.get("A股简称", "")).strip()
                if code:
                    stocks.append({"code": code, "name": name})
    except Exception as e:
        errors.append(f"深交所:{e}")

    # 数据源3：东财全 A 股兜底（覆盖沪深；海外时上/深交所可能不可用，虽慢但可靠）
    has_sh = any(s["code"].startswith("6") for s in stocks)
    has_sz = any(s["code"].startswith(("0", "3")) for s in stocks)
    if not (has_sh and has_sz):
        try:
            df = ak.stock_info_a_code_name()
            if df is not None and not df.empty:
                seen = {s["code"] for s in stocks}
                for _, row in df.iterrows():
                    code = str(row.get("code", "")).strip()
                    name = str(row.get("name", "")).strip()
                    if code and code not in seen:
                        stocks.append({"code": code, "name": name})
        except Exception as e:
            errors.append(f"东财全A股:{e}")

    if not stocks:
        raise RuntimeError(f"所有股票列表数据源均失败: {'; '.join(errors)}")
    return stocks


def _get_stock_list():
    """获取A股股票列表（带缓存）"""
    global _stock_list_cache, _cache_time
    now = datetime.datetime.now()

    if _stock_list_cache is not None and _cache_time is not None:
        if (now - _cache_time).total_seconds() < _CACHE_DURATION:
            return _stock_list_cache

    with _stock_list_lock:
        now = datetime.datetime.now()
        if _stock_list_cache is not None and _cache_time is not None:
            if (now - _cache_time).total_seconds() < _CACHE_DURATION:
                return _stock_list_cache
        try:
            stocks = _fetch_stock_list()
            _stock_list_cache = stocks
            _cache_time = now
            return stocks
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            if _stock_list_cache is not None:
                return _stock_list_cache
            return []


def search_stock(keyword: str, limit: int = 10) -> List[StockSearchItem]:
    """
    模糊搜索股票
    :param keyword: 关键词（代码或名称）
    :param limit: 返回数量上限
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    stocks = _get_stock_list()
    results = []

    for s in stocks:
        if keyword.lower() in s["code"].lower() or keyword in s["name"]:
            results.append(StockSearchItem(code=s["code"], name=s["name"]))
            if len(results) >= limit:
                break

    return results


def _normalize_code(code: str) -> str:
    """标准化股票代码，补全6位"""
    code = re.sub(r'\D', '', code)
    return code.zfill(6)


@_retry(max_retries=5, delay=3)
def _fetch_spot_em():
    """获取全市场实时行情（带重试）"""
    ak = _get_ak()
    return ak.stock_zh_a_spot_em()


def _get_stock_name_from_cache(code: str) -> str:
    """仅从已加载的股票列表获取名称，不因行情请求触发全量列表加载。"""
    code = _normalize_code(code)
    with _stock_list_lock:
        stocks = _stock_list_cache or []
    for s in stocks:
        if s["code"] == code:
            return s["name"]
    return code


def _get_cached_daily_kline(code: str, lookback_days: int):
    """读取带短 TTL 的日 K 原始数据，并合并同一股票的并发请求。"""
    code = _normalize_code(code)
    bucket = max(lookback_days, 300)
    key = (code, bucket)
    now = time.monotonic()
    with _kline_cache_lock:
        cached = _kline_cache.get(key)
        if cached and now - cached["fetched_at"] < _KLINE_CACHE_DURATION:
            return cached["df"].copy()
        lock = _kline_fetch_locks.setdefault(key, threading.Lock())

    with lock:
        now = time.monotonic()
        with _kline_cache_lock:
            cached = _kline_cache.get(key)
            if cached and now - cached["fetched_at"] < _KLINE_CACHE_DURATION:
                return cached["df"].copy()
        start_date = (datetime.datetime.now() - datetime.timedelta(days=bucket)).strftime("%Y%m%d")
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        try:
            df = _fetch_kline(code, "daily", start_date, end_date)
            if df is None or df.empty:
                raise RuntimeError("K线为空")
            with _kline_cache_lock:
                _kline_cache[key] = {"fetched_at": time.monotonic(), "df": df.copy()}
            return df.copy()
        except Exception:
            with _kline_cache_lock:
                cached = _kline_cache.get(key)
            if cached and time.monotonic() - cached["fetched_at"] < _KLINE_STALE_DURATION:
                return cached["df"].copy()
            raise
        finally:
            with _kline_cache_lock:
                if _kline_fetch_locks.get(key) is lock:
                    _kline_fetch_locks.pop(key, None)


def _stock_info_from_kline(code: str, df, name: str) -> Optional[StockInfo]:
    """从日 K 原始数据构造行情摘要。"""
    if df is None or df.empty:
        return None
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    close = float(latest.get("收盘", 0))
    prev_close = float(prev.get("收盘", 0))
    change_amount = close - prev_close
    return StockInfo(
        code=code, name=name, price=close,
        change_pct=round((change_amount / prev_close * 100) if prev_close else 0, 2),
        change_amount=round(change_amount, 2),
        open=float(latest.get("开盘", 0)), pre_close=prev_close,
        high=float(latest.get("最高", 0)), low=float(latest.get("最低", 0)),
        volume=float(latest.get("成交量", 0)),
        amount=float(latest.get("成交额", 0)) if "成交额" in df.columns else 0,
    )


def get_stock_info(code: str) -> Optional[StockInfo]:
    """获取股票行情信息，优先复用共享日 K 缓存。"""
    code = _normalize_code(code)
    try:
        df = _get_cached_daily_kline(code, 300)
        return _stock_info_from_kline(code, df, _get_stock_name_from_cache(code))
    except Exception as e:
        print(f"获取股票 {code} 行情（K线）失败: {e}")
        return None


def _fetch_kline(code: str, period: str, start_date: str, end_date: str):
    """
    获取K线原始数据（优先新浪，备用东方财富）
    新浪接口快且稳定，作为主力数据源
    """
    ak = _get_ak()

    # 数据源1：新浪财经（快且稳）
    try:
        # 新浪代码需要加市场前缀：sh600519 / sz000001
        prefix = "sh" if code.startswith(("6", "9")) else "sz"
        symbol = f"{prefix}{code}"
        df = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        if df is not None and not df.empty:
            # 统一列名：新浪英文 -> 东财中文
            col_map = {
                "date": "日期",
                "open": "开盘",
                "high": "最高",
                "low": "最低",
                "close": "收盘",
                "volume": "成交量",
                "amount": "成交额",
            }
            df = df.rename(columns=col_map)
            # 成交量：新浪单位是股，东财接口是手（100股），统一成手
            if "成交量" in df.columns:
                df["成交量"] = df["成交量"] / 100
            return df
    except Exception as e:
        print(f"新浪K线失败: {e}，尝试东方财富...")

    # 数据源2：东方财富（备用）
    @_retry(max_retries=3, delay=2)
    def _try_em():
        return ak.stock_zh_a_hist(
            symbol=code, period=period,
            start_date=start_date, end_date=end_date, adjust="qfq"
        )
    try:
        return _try_em()
    except Exception as e:
        raise RuntimeError(f"所有K线数据源均失败: {e}")


def _resample_kline(df, period: str):
    """将日K数据聚合为周K或月K"""
    pd = _get_pd()
    # 确保日期列是 datetime 类型
    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.set_index("日期")

    # 定义聚合规则
    agg_dict = {
        "开盘": "first",
        "收盘": "last",
        "最高": "max",
        "最低": "min",
        "成交量": "sum",
        "成交额": "sum",
    }

    if period == "weekly":
        # 周K：以周一为一周开始
        resampled = df.resample("W-MON", label="left", closed="left").agg(agg_dict)
    elif period == "monthly":
        # 月K
        resampled = df.resample("ME").agg(agg_dict)
    else:
        return df

    resampled = resampled.dropna(subset=["收盘"])
    resampled = resampled.reset_index()
    resampled["日期"] = resampled["日期"].dt.strftime("%Y-%m-%d")

    return resampled


def get_kline_data(code: str, period: str = "daily", days: int = 250) -> Optional[KLineData]:
    """
    获取K线数据
    :param code: 股票代码
    :param period: 周期 daily/weekly/monthly
    :param days: 获取天数
    """
    code = _normalize_code(code)
    try:
        df = _get_cached_daily_kline(code, max(days + 50, 300))

        if df.empty:
            return None

        # 如果是周K/月K，用日K数据聚合（新浪接口只有日K）
        if period != "daily":
            df = _resample_kline(df, period)

        # 取最近 days 条
        df = df.tail(days).reset_index(drop=True)

        pd = _get_pd()
        closes = df["收盘"].astype(float)
        highs = df["最高"].astype(float)
        lows = df["最低"].astype(float)

        # 计算均线
        ma5 = closes.rolling(window=5).mean()
        ma10 = closes.rolling(window=10).mean()
        ma20 = closes.rolling(window=20).mean()

        # 计算 MACD
        dif, dea, macd = _calc_macd(closes)

        # 计算 KDJ
        kdj_k, kdj_d, kdj_j = _calc_kdj(highs, lows, closes)

        # 计算 RSI
        rsi6 = _calc_rsi(closes, 6)
        rsi12 = _calc_rsi(closes, 12)
        rsi24 = _calc_rsi(closes, 24)

        kline_list = []
        for i, row in df.iterrows():
            kline_list.append(KLineItem(
                date=str(row.get("日期", "")),
                open=float(row.get("开盘", 0)),
                close=float(row.get("收盘", 0)),
                high=float(row.get("最高", 0)),
                low=float(row.get("最低", 0)),
                volume=float(row.get("成交量", 0)),
                ma5=round(float(ma5.iloc[i]), 2) if pd.notna(ma5.iloc[i]) else None,
                ma10=round(float(ma10.iloc[i]), 2) if pd.notna(ma10.iloc[i]) else None,
                ma20=round(float(ma20.iloc[i]), 2) if pd.notna(ma20.iloc[i]) else None,
                dif=round(float(dif.iloc[i]), 3) if pd.notna(dif.iloc[i]) else None,
                dea=round(float(dea.iloc[i]), 3) if pd.notna(dea.iloc[i]) else None,
                macd=round(float(macd.iloc[i]), 3) if pd.notna(macd.iloc[i]) else None,
                kdj_k=round(float(kdj_k.iloc[i]), 2) if pd.notna(kdj_k.iloc[i]) else None,
                kdj_d=round(float(kdj_d.iloc[i]), 2) if pd.notna(kdj_d.iloc[i]) else None,
                kdj_j=round(float(kdj_j.iloc[i]), 2) if pd.notna(kdj_j.iloc[i]) else None,
                rsi6=round(float(rsi6.iloc[i]), 2) if pd.notna(rsi6.iloc[i]) else None,
                rsi12=round(float(rsi12.iloc[i]), 2) if pd.notna(rsi12.iloc[i]) else None,
                rsi24=round(float(rsi24.iloc[i]), 2) if pd.notna(rsi24.iloc[i]) else None,
            ))

        # 从缓存获取股票名称（不额外发请求）
        stock_name = _get_stock_name_from_cache(code)

        return KLineData(
            code=code,
            name=stock_name,
            kline=kline_list
        )
    except Exception as e:
        print(f"获取股票 {code} K线数据失败: {e}")
        return None


def get_monitor_snapshot(code: str, days: int = 90) -> MonitorSnapshot:
    """单次读取日 K，构造盘中监控所需的行情、指标和收益快照。"""
    data = get_kline_data(code, period="daily", days=days)
    if not data or len(data.kline) < 2:
        raise RuntimeError(f"股票 {code} 有效 K 线数据不足")

    rows = [row for row in data.kline if isfinite(row.close) and row.close > 0]
    if len(rows) < 2:
        raise RuntimeError(f"股票 {code} 有效 K 线数据不足")
    latest = rows[-1]
    previous = rows[-2]
    previous_close = previous.close
    change_amount = latest.close - previous_close
    change_pct = change_amount / previous_close * 100 if previous_close else None
    prior_highs = [row.high for row in rows[-21:-1] if isfinite(row.high) and row.high > 0]
    high20_distance_pct = None
    if prior_highs and max(prior_highs) > 0:
        high20_distance_pct = (latest.close / max(prior_highs) - 1) * 100

    def period_return(period: int) -> float | None:
        if len(rows) <= period or not isfinite(rows[-period - 1].close) or rows[-period - 1].close == 0:
            return None
        return (latest.close / rows[-period - 1].close - 1) * 100

    return MonitorSnapshot(
        code=data.code,
        name=data.name,
        rows=rows,
        kline=rows,
        quote=MonitorQuote(
            price=latest.close,
            change_pct=round(change_pct, 2) if change_pct is not None else None,
            change_amount=round(change_amount, 2),
            volume=latest.volume,
            source="kline",
            as_of=latest.date,
        ),
        indicators=MonitorIndicators(
            ma5=latest.ma5,
            ma10=latest.ma10,
            ma20=latest.ma20,
            dif=latest.dif,
            dea=latest.dea,
            macd=latest.macd,
            rsi6=latest.rsi6,
            rsi12=latest.rsi12,
            rsi24=latest.rsi24,
            high20_distance_pct=round(high20_distance_pct, 2) if high20_distance_pct is not None else None,
        ),
        metrics=MonitorMetrics(
            return_5d_pct=_rounded_or_none(period_return(5)),
            return_20d_pct=_rounded_or_none(period_return(20)),
        ),
        sparkline=[{"date": row.date, "close": row.close} for row in rows[-30:]],
        fetched_at=datetime.datetime.now(datetime.timezone.utc),
    )


def _rounded_or_none(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def _parse_value_with_unit(val_str) -> Optional[float]:
    """
    解析带单位的数值字符串，如 '4172.63万'、'1.97亿'、'3.14'、'--'
    返回纯数字（单位统一为亿）
    """
    if val_str is None:
        return None
    s = str(val_str).strip()
    if not s or s in ('--', '-', 'NaN', 'nan', 'None', 'null'):
        return None
    try:
        if '亿' in s:
            num = float(s.replace('亿', ''))
            return num
        elif '万' in s:
            num = float(s.replace('万', ''))
            return num / 10000  # 万转亿
        else:
            return float(s)
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> Optional[float]:
    """
    安全转 float，空值/NaN 返回 None
    支持带 % 的字符串（自动去掉 % 后转换）
    """
    if val is None:
        return None
    pd = _get_pd()
    try:
        s = str(val).strip()
        if s.endswith('%'):
            s = s[:-1].strip()
        f = float(s)
        if pd.isna(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _fetch_financial_data(code: str) -> Optional[FinancialData]:
    """
    获取财务数据（多数据源 fallback）
    估值指标：stock_value_em（主力）
    财务指标：stock_financial_abstract_ths（主力）+ stock_financial_analysis_indicator（备用）
    """
    code = _normalize_code(code)
    ak = _get_ak()
    pd = _get_pd()
    result = FinancialData(code=code, name=code)

    try:
        # 从缓存获取股票名称
        result.name = _get_stock_name_from_cache(code)

        # ========== 估值指标（PE/PB/总市值）==========
        # 数据源1：stock_value_em（东财估值分析，含 PE/PB/总市值 历史数据）
        try:
            df = ak.stock_value_em(symbol=code)
            if df is not None and not df.empty:
                latest = df.iloc[-1]  # 最新一期在最后
                result.pe = _safe_float(latest.get("PE(TTM)"))
                result.pb = _safe_float(latest.get("市净率"))
                total_mv = _safe_float(latest.get("总市值"))
                if total_mv is not None:
                    result.total_mv = total_mv / 1e8  # 元转亿
        except Exception as e:
            print(f"获取估值指标(value_em)失败: {e}")

        # ========== 财务指标 ==========
        # 数据源1：同花顺财务摘要（主力，数据完整且准确）
        try:
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            if df is not None and not df.empty:
                latest = df.iloc[-1]  # 最新一期在最后

                # 报告期
                if "报告期" in latest:
                    result.report_date = str(latest["报告期"])

                # ROE（净资产收益率）
                for col in ["净资产收益率", "净资产收益率-摊薄", "净资产收益率(%)"]:
                    if col in latest:
                        result.roe = _safe_float(latest[col])
                        if result.roe is not None:
                            break

                # 净利润（带单位，解析为亿）
                for col in ["净利润", "扣非净利润"]:
                    if col in latest:
                        val = _parse_value_with_unit(latest[col])
                        if val is not None:
                            result.net_profit = val
                            break

                # 营业收入（带单位，解析为亿）
                for col in ["营业总收入", "营业收入"]:
                    if col in latest:
                        val = _parse_value_with_unit(latest[col])
                        if val is not None:
                            result.revenue = val
                            break

                # 毛利率
                for col in ["销售毛利率", "销售毛利率(%)", "毛利率"]:
                    if col in latest:
                        result.gross_margin = _safe_float(latest[col])
                        if result.gross_margin is not None:
                            break

                # 净利率
                for col in ["销售净利率", "销售净利率(%)", "净利率"]:
                    if col in latest:
                        result.net_margin = _safe_float(latest[col])
                        if result.net_margin is not None:
                            break
        except Exception as e:
            print(f"获取财务指标(ths_abstract)失败: {e}")

            # 数据源2：东财财务分析指标（备用）
            if result.roe is None and result.net_profit is None:
                try:
                    df = ak.stock_financial_analysis_indicator(symbol=code)
                    if df is not None and not df.empty:
                        latest = df.iloc[-1]  # 最新一期在最后

                        # 报告期
                        if "日期" in latest:
                            result.report_date = str(latest["日期"])

                        # ROE
                        for col in ["净资产收益率(%)", "净资产收益率", "加权净资产收益率(%)"]:
                            if col in latest:
                                result.roe = _safe_float(latest[col])
                                if result.roe is not None:
                                    break

                        # 净利润（东财单位是元）
                        for col in ["净利润(亿元)", "净利润", "归属于母公司所有者的净利润"]:
                            if col in latest:
                                val = _safe_float(latest[col])
                                if val is not None:
                                    result.net_profit = val
                                    break

                        # 营业收入
                        for col in ["营业收入(亿元)", "营业收入"]:
                            if col in latest:
                                val = _safe_float(latest[col])
                                if val is not None:
                                    result.revenue = val
                                    break

                        # 毛利率
                        for col in ["销售毛利率(%)", "毛利率"]:
                            if col in latest:
                                result.gross_margin = _safe_float(latest[col])
                                if result.gross_margin is not None:
                                    break

                        # 净利率
                        for col in ["销售净利率(%)", "净利率"]:
                            if col in latest:
                                result.net_margin = _safe_float(latest[col])
                                if result.net_margin is not None:
                                    break
                except Exception as e2:
                    print(f"获取财务指标(em_analysis)失败: {e2}")

        return result
    except Exception as e:
        print(f"获取股票 {code} 财务数据失败: {e}")
        return result
def get_financial_data(code: str) -> Optional[FinancialData]:
    """获取财务数据，使用短 TTL 缓存减少详情页并发请求。"""
    code = _normalize_code(code)
    now = time.monotonic()
    with _FINANCIAL_CACHE_LOCK:
        cached = _FINANCIAL_CACHE.get(code)
        if cached and now - cached["fetched_at"] < _FINANCIAL_CACHE_DURATION:
            return cached["data"]
    try:
        data = _fetch_financial_data(code)
    except Exception as e:
        print(f"获取股票 {code} 财务数据失败: {e}")
        return None
    with _FINANCIAL_CACHE_LOCK:
        _FINANCIAL_CACHE[code] = {"fetched_at": time.monotonic(), "data": data}
    return data


def _calc_macd(closes, fast=12, slow=26, signal=9):
    """
    计算 MACD 指标
    返回: (DIF, DEA, MACD柱)
    MACD柱 = 2 * (DIF - DEA)
    """
    pd = _get_pd()
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = 2 * (dif - dea)
    return dif, dea, macd


def _calc_kdj(highs, lows, closes, n=9, m1=3, m2=3):
    """
    计算 KDJ 指标
    返回: (K, D, J)
    """
    pd = _get_pd()

    # 计算 RSV
    lowest_low = lows.rolling(window=n, min_periods=1).min()
    highest_high = highs.rolling(window=n, min_periods=1).max()
    rsv = (closes - lowest_low) / (highest_high - lowest_low) * 100
    rsv = rsv.fillna(50)  # 初始值用50

    # K = 前一日K * (m1-1)/m1 + 当日RSV * 1/m1
    k = pd.Series(index=closes.index, dtype=float)
    d = pd.Series(index=closes.index, dtype=float)
    prev_k = 50.0
    prev_d = 50.0

    for i in range(len(rsv)):
        k_val = prev_k * (m1 - 1) / m1 + rsv.iloc[i] * 1 / m1
        d_val = prev_d * (m2 - 1) / m2 + k_val * 1 / m2
        k.iloc[i] = k_val
        d.iloc[i] = d_val
        prev_k = k_val
        prev_d = d_val

    j = 3 * k - 2 * d
    return k, d, j


def _calc_rsi(closes, period=14):
    """
    计算 RSI 指标（相对强弱指数）
    """
    pd = _get_pd()
    delta = closes.diff()

    # 分离涨跌
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # 用 EMA 计算平均涨跌幅（Wilder's smoothing）
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    # 避免除零
    rs = avg_gain / avg_loss.replace(0, float('nan'))
    rsi = 100 - (100 / (1 + rs))

    # avg_loss 为 0 时 RSI = 100
    rsi = rsi.fillna(100)
    return rsi
