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
    获取板块成分股
    :param board_name: 板块名称
    :param board_type: industry / concept
    """
    ak = _get_ak()
    errors = []

    # 数据源：东方财富
    try:
        if board_type == "industry":
            df = _fetch_board_industry_cons_em(ak, board_name)
        else:
            df = _fetch_board_concept_cons_em(ak, board_name)

        return _parse_board_stocks(df)
    except Exception as e:
        errors.append(f"东财:{e}")

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
            total_turnover=_get_float(row, "总市值", "总成交额", "成交额"),
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
    """解析板块成分股数据"""
    result = []
    for _, row in df.iterrows():
        result.append(BoardStock(
            code=str(row.get("代码", row.get("股票代码", ""))),
            name=str(row.get("名称", row.get("股票简称", ""))),
            price=float(row.get("最新价", 0) or 0),
            change_pct=float(row.get("涨跌幅", 0) or 0),
            change_amount=float(row.get("涨跌额", 0) or 0),
            turnover_rate=float(row.get("换手率", 0) or 0),
            pe=float(row.get("市盈率", 0) or 0) if "市盈率" in df.columns else None,
            total_mv=float(row.get("总市值", 0) or 0) / 100000000 if "总市值" in df.columns else None,
        ))
    result.sort(key=lambda x: x.change_pct, reverse=True)
    return result
