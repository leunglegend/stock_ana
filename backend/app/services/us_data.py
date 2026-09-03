"""美股收盘行情服务（方案 B 主链路 = 新浪静态日线）。

新浪静态日线在美股盘中也不更新当日 bar（实测 ET 午间请求仍返回上一
交易日完整日量），天然是"最近已入库交易日收盘"口径 —— 与美股页"收盘
复盘"定位一致。板块聚合依赖静态成分表（us_universe）。
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.models.schemas import UsConstituent, UsIndexQuote, UsSector
from app.services import stock_data

# (新浪代码, 展示 symbol, 中文名)；前 3 为 3 大指数，路由取 .DJI/.INX/.IXIC
US_INDEX_SYMBOLS = (
    (".INX", "SPX", "标普500"),
    (".IXIC", "IXIC", "纳斯达克"),
    (".DJI", "DJI", "道琼斯"),
    (".NDX", "NDX", "纳斯达克100"),
    (".SOX", "SOX", "费城半导体"),
)
_MAJOR_INDEX_SYMBOLS = ("DJI", "SPX", "IXIC")  # 摘要/卡片展示用 3 大指数


def _close_pct(price: float, prev_close: float) -> tuple:
    change = price - prev_close
    pct = (price / prev_close - 1) * 100 if prev_close else 0.0
    return change, pct


@stock_data._retry(max_retries=2, delay=1)
def _index_frame(ak, symbol: str):
    return ak.index_us_stock_sina(symbol=symbol)


def _frame_latest(frame):
    """frame 按 date 升序排序后返回 (date, close, prev_close)；不足两根返回 None。"""
    df = frame.sort_values("date").reset_index(drop=True)
    if len(df) < 2:
        return None
    last, prev = df.iloc[-1], df.iloc[-2]
    return str(last["date"]), float(last["close"]), float(prev["close"])


def fetch_index_quotes(ak=None) -> list:
    """拉 5 个美股指数的收盘涨跌（单指数失败跳过，不拖垮整体）。"""
    ak = ak or stock_data._get_ak()
    quotes = []
    for code, symbol, cn in US_INDEX_SYMBOLS:
        try:
            latest = _frame_latest(_index_frame(ak, code))
            if not latest:
                continue
            date, close, prev = latest
            change, pct = _close_pct(close, prev)
            quotes.append(UsIndexQuote(symbol=symbol, name=cn, value=close,
                                       change_amount=change, change_pct=pct))
        except Exception as e:
            print(f"[us] 指数 {code} 拉取失败: {e}")
    return quotes


def fetch_index_asof(ak=None) -> Optional[str]:
    """轻量探测最新美东交易日（标普500 日线最近 bar date，1 个请求）。"""
    ak = ak or stock_data._get_ak()
    try:
        latest = _frame_latest(_index_frame(ak, ".INX"))
        return latest[0] if latest else None
    except Exception as e:
        print(f"[us] as_of 探测失败: {e}")
        return None
