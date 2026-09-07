"""
板块数据服务 - 行业板块、概念板块
多数据源 fallback + 缓存
"""
import time
import datetime
from typing import List, Optional

from app.models.schemas import BoardInfo, BoardStock
from app.services.stock_data import _get_ak, _retry


# 板块列表缓存
_board_cache = {
    "industry": {"data": None, "time": None},
    "concept": {"data": None, "time": None},
}
_CACHE_TTL = 300  # 缓存5分钟

# 板块成分股缓存（按板块名称缓存，避免频繁请求同一板块）
_board_stocks_cache = {}
_BOARD_STOCKS_CACHE_TTL = 120  # 缓存2分钟


def get_industry_boards() -> Optional[List[BoardInfo]]:
    """
    获取行业板块列表（带涨跌幅）
    多数据源 fallback：东财 → 同花顺汇总 → 同花顺名称
    """
    cache = _board_cache["industry"]
    now = time.time()
    if cache["data"] and cache["time"] and (now - cache["time"]) < _CACHE_TTL:
        return cache["data"]

    ak = _get_ak()
    errors = []

    # 数据源1：东方财富
    try:
        df = _fetch_board_industry_em(ak)
        result = _parse_board_em(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"东财:{e}")

    # 数据源2：同花顺行业汇总（推荐，数据完整含涨跌幅/涨跌家数/领涨股）
    try:
        df = _fetch_board_industry_summary_ths(ak)
        result = _parse_board_ths_summary(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"同花顺汇总:{e}")

    # 数据源3：同花顺名称列表（只有名称代码，无涨跌幅，最次备选）
    try:
        df = _fetch_board_industry_ths(ak)
        result = _parse_board_ths(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"同花顺名称:{e}")

    print(f"获取行业板块失败: {'; '.join(errors)}")
    return cache["data"]  # 返回缓存（即使过期了也返回旧数据）


def get_concept_boards() -> Optional[List[BoardInfo]]:
    """
    获取概念板块列表（带涨跌幅）
    多数据源 fallback：东财 → 同花顺汇总 → 同花顺名称
    """
    cache = _board_cache["concept"]
    now = time.time()
    if cache["data"] and cache["time"] and (now - cache["time"]) < _CACHE_TTL:
        return cache["data"]

    ak = _get_ak()
    errors = []

    # 数据源1：东方财富-概念板块名称列表（含涨跌幅）
    try:
        df = _fetch_board_concept_em(ak)
        result = _parse_board_em(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"东财名称:{e}")

    # 数据源2：东方财富-概念板块实时行情（备用）
    try:
        df = _fetch_board_concept_spot_em(ak)
        result = _parse_board_em(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"东财实时:{e}")

    # 数据源3：同花顺概念汇总（只有名称/龙头股/事件，无涨跌幅，次备选）
    try:
        df = _fetch_board_concept_summary_ths(ak)
        result = _parse_board_ths(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"同花顺汇总:{e}")

    # 数据源4：同花顺名称列表（只有名称代码，无涨跌幅，最次备选）
    try:
        df = _fetch_board_concept_ths(ak)
        result = _parse_board_ths(df)
        if result:
            cache["data"] = result
            cache["time"] = now
            return result
    except Exception as e:
        errors.append(f"同花顺名称:{e}")

    print(f"获取概念板块失败: {'; '.join(errors)}")
    return cache["data"]


def get_board_stocks(board_name: str, board_type: str = "industry") -> Optional[List[BoardStock]]:
    """
    获取板块成分股（多数据源 fallback + 缓存）
    :param board_name: 板块名称
    :param board_type: industry / concept
    """
    import concurrent.futures

    cache_key = f"{board_type}:{board_name}"
    now = time.time()

    # 先查缓存
    cached = _board_stocks_cache.get(cache_key)
    if cached and (now - cached["time"]) < _BOARD_STOCKS_CACHE_TTL:
        return cached["data"]

    ak = _get_ak()
    errors = []
    timeout_seconds = 12  # 单数据源超时时间，避免接口卡住

    def _fetch_em():
        """数据源1：东方财富成分股"""
        if board_type == "industry":
            return _fetch_board_industry_cons_em(ak, board_name)
        else:
            return _fetch_board_concept_cons_em(ak, board_name)

    def _fetch_sina():
        """数据源2：新浪行业成分股。"""
        if board_type != "industry":
            return None
        return _fetch_board_stocks_sina(ak, board_name)

    sources = (
        [("新浪行业", _fetch_sina), ("东方财富", _fetch_em)]
        if board_type == "industry"
        else [("东方财富", _fetch_em)]
    )
    for source_name, fetch_fn in sources:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(fetch_fn)
                df = future.result(timeout=timeout_seconds)
            result = _parse_board_stocks(df)
            if result:
                # 写入缓存
                _board_stocks_cache[cache_key] = {"data": result, "time": now}
                return result
            else:
                errors.append(f"{source_name}: 返回空数据")
        except concurrent.futures.TimeoutError:
            errors.append(f"{source_name}: 超时({timeout_seconds}s)")
        except Exception as e:
            errors.append(f"{source_name}: {e}")

    # 全部失败时，返回过期缓存（如果有的话）
    if cached:
        print(f"获取板块成分股 [{board_name}] 全部数据源失败，返回过期缓存: {'; '.join(errors)}")
        return cached["data"]

    print(f"获取板块成分股失败 [{board_name}]: {'; '.join(errors)}")
    return None


@_retry(max_retries=3, delay=2)
def _fetch_board_industry_em(ak):
    """东方财富-行业板块列表"""
    return ak.stock_board_industry_name_em()


@_retry(max_retries=3, delay=2)
def _fetch_board_concept_em(ak):
    """东方财富-概念板块列表"""
    return ak.stock_board_concept_name_em()


@_retry(max_retries=2, delay=2)
def _fetch_board_concept_spot_em(ak):
    """东方财富-概念板块实时行情（备用数据源）"""
    return ak.stock_board_concept_spot_em()


@_retry(max_retries=2, delay=2)
def _fetch_board_industry_cons_em(ak, name):
    """东方财富-行业板块成分股"""
    return ak.stock_board_industry_cons_em(symbol=name)


@_retry(max_retries=2, delay=2)
def _fetch_board_concept_cons_em(ak, name):
    """东方财富-概念板块成分股"""
    return ak.stock_board_concept_cons_em(symbol=name)


@_retry(max_retries=2, delay=2)
def _fetch_board_industry_summary_ths(ak):
    """同花顺-行业板块汇总（主力数据源，含涨跌幅/涨跌家数/领涨股）"""
    return ak.stock_board_industry_summary_ths()


def _fetch_board_industry_ths(ak):
    """同花顺-行业板块名称列表（仅名称代码，备用）"""
    return ak.stock_board_industry_name_ths()


@_retry(max_retries=2, delay=2)
def _fetch_board_concept_summary_ths(ak):
    """同花顺-概念板块汇总（主力数据源，含涨跌幅/领涨股）"""
    return ak.stock_board_concept_summary_ths()


def _fetch_board_concept_ths(ak):
    """同花顺-概念板块名称列表（仅名称代码，备用）"""
    return ak.stock_board_concept_name_ths()


_SINA_INDUSTRY_ALIASES = {
    "种植业与林业": ("农业", "林业"),
}


def _sina_industry_names(board_name: str):
    aliases = _SINA_INDUSTRY_ALIASES.get(board_name)
    return aliases or (board_name,)


def _fetch_board_stocks_sina(ak, board_name: str):
    """按行业名称从新浪板块列表匹配并合并成分股。"""
    import pandas as pd

    sectors = ak.stock_sector_spot(indicator="行业")
    requested = _sina_industry_names(board_name)
    matched = sectors[sectors["板块"].astype(str).isin(requested)]
    if matched.empty:
        raise ValueError(f"新浪行业未匹配到板块: {board_name}")
    frames = [ak.stock_sector_detail(sector=row["label"]) for _, row in matched.iterrows()]
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["code"])


def _parse_board_em(df) -> List[BoardInfo]:
    """解析东方财富板块数据（兼容多种列名）"""
    # 兼容不同版本 AKShare 的列名差异
    def _get(row, *candidates, default=""):
        for col in candidates:
            if col in row and row.get(col) is not None:
                val = row.get(col)
                # pandas 的 nan 判断
                try:
                    import math
                    if isinstance(val, float) and math.isnan(val):
                        continue
                except Exception:
                    pass
                return val
        return default

    def _get_float(row, *candidates, default=0.0):
        val = _get(row, *candidates, default=None)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _get_int(row, *candidates, default=0):
        val = _get(row, *candidates, default=None)
        if val is None or val == "":
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    result = []
    for _, row in df.iterrows():
        name = str(_get(row, "板块名称", "名称", "概念名称", "行业名称")).strip()
        # 跳过空名称
        if not name or name == "nan":
            continue
        result.append(BoardInfo(
            name=name,
            change_pct=_get_float(row, "涨跌幅", "今日涨幅", "涨幅"),
            change_amount=_get_float(row, "涨跌额", "涨跌"),
            # 东财返回的是元，前端与 schema 口径统一为亿
            total_turnover=_get_float(row, "总市值", "总成交额", "成交额") / 100000000,
            turnover_rate=_get_float(row, "换手率"),
            leading_stock=str(_get(row, "领涨股票", "领涨股", "领涨", "龙头股")).strip(),
            leading_change=_get_float(row, "领涨股涨跌幅", "领涨股涨幅", "领涨涨幅"),
            stock_count=_get_int(row, "股票数", "公司家数", "上涨家数", "下跌家数") + _get_int(row, "下跌家数"),
            rise_count=_get_int(row, "上涨家数", "上涨"),
            fall_count=_get_int(row, "下跌家数", "下跌"),
        ))
    # 按涨跌幅排序（从高到低）
    result.sort(key=lambda x: x.change_pct, reverse=True)
    return result


def _parse_board_ths(df) -> List[BoardInfo]:
    """解析同花顺板块数据（兼容多种列名格式）"""
    # 通用的取值辅助函数
    def _get(row, *candidates, default=""):
        for col in candidates:
            if col in row and row.get(col) is not None:
                val = row.get(col)
                try:
                    import math
                    if isinstance(val, float) and math.isnan(val):
                        continue
                except Exception:
                    pass
                return val
        return default

    def _get_float(row, *candidates, default=0.0):
        val = _get(row, *candidates, default=None)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _get_int(row, *candidates, default=0):
        val = _get(row, *candidates, default=None)
        if val is None or val == "":
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    result = []
    for _, row in df.iterrows():
        name = str(_get(row, "板块", "板块名称", "概念名称", "name", "名称")).strip()
        if not name or name == "nan":
            continue
        rise = _get_int(row, "上涨家数", "上涨")
        fall = _get_int(row, "下跌家数", "下跌")
        result.append(BoardInfo(
            name=name,
            change_pct=_get_float(row, "涨跌幅", "今日涨幅", "涨幅"),
            change_amount=_get_float(row, "涨跌额", "涨跌"),
            total_turnover=_get_float(row, "总成交额", "总市值", "总成交量", "总手"),
            turnover_rate=_get_float(row, "换手率"),
            leading_stock=str(_get(row, "领涨股", "领涨股票", "龙头股")).strip(),
            leading_change=_get_float(row, "领涨股-涨跌幅", "领涨股涨幅", "领涨股涨跌幅"),
            stock_count=rise + fall or _get_int(row, "公司家数", "股票数"),
            rise_count=rise,
            fall_count=fall,
        ))
    result.sort(key=lambda x: x.change_pct, reverse=True)
    return result


def _parse_board_ths_summary(df) -> List[BoardInfo]:
    """解析同花顺行业板块汇总数据（列名：序号、板块、涨跌幅、总成交量、总成交额、净流入、上涨家数、下跌家数、均价、领涨股、领涨股-最新价、领涨股-涨跌幅）"""
    return _parse_board_ths(df)


def _parse_board_stocks(df) -> List[BoardStock]:
    """解析板块成分股数据（兼容东财/同花顺等多数据源列名）"""
    import math

    def _get(row, *candidates, default=""):
        for col in candidates:
            if col in row and row.get(col) is not None:
                val = row.get(col)
                try:
                    if isinstance(val, float) and math.isnan(val):
                        continue
                except Exception:
                    pass
                return val
        return default

    def _get_float(row, *candidates, default=0.0):
        val = _get(row, *candidates, default=None)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    result = []
    for _, row in df.iterrows():
        code = str(_get(row, "代码", "股票代码", "证券代码", "A股代码", "code")).strip()
        name = str(_get(row, "名称", "股票简称", "证券简称", "A股简称", "name")).strip()
        # 跳过无效行
        if not code or code == "nan" or not name or name == "nan":
            continue
        result.append(BoardStock(
            code=code,
            name=name,
            price=_get_float(row, "最新价", "现价", "收盘", "trade"),
            change_pct=_get_float(row, "涨跌幅", "涨幅", "涨跌幅(%)", "changepercent"),
            change_amount=_get_float(row, "涨跌额", "涨跌", "pricechange"),
            turnover_rate=_get_float(row, "换手率", "换手", "turnoverratio"),
            pe=_parse_board_pe(row, df.columns, _get_float),
            total_mv=_parse_board_mv(row, df.columns, _get_float),
        ))
    # 按涨跌幅排序（从高到低）
    result.sort(key=lambda x: x.change_pct, reverse=True)
    return result


def _parse_board_pe(row, columns, get_float):
    if "per" in columns:
        return get_float(row, "per")
    if "市盈率" in columns or "市盈率(动态)" in columns:
        return get_float(row, "市盈率", "市盈率(动态)")
    return None


def _parse_board_mv(row, columns, get_float):
    if "mktcap" in columns:
        return get_float(row, "mktcap") / 10000
    if "总市值" in columns or "市价总值" in columns:
        return get_float(row, "总市值", "市价总值") / 100000000
    return None
