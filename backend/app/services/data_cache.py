"""
数据缓存服务 - 定时刷新热点数据，请求零延迟返回
"""
import time
import threading
from typing import Optional, List

from app.models.schemas import BoardInfo, MarketSummary
from app.services import board_data, market_data


# 缓存数据
_cache = {
    "industry_boards": {"data": None, "time": 0, "loading": False},
    "concept_boards": {"data": None, "time": 0, "loading": False},
    "market_summary": {"data": None, "time": 0, "loading": False},
}

# 刷新间隔（秒）
REFRESH_INTERVAL = {
    "industry_boards": 120,   # 板块数据 2 分钟刷新一次
    "concept_boards": 120,
    "market_summary": 60,     # 市场概览 1 分钟刷新一次
}

_refresh_thread = None
_stop_flag = threading.Event()


def _refresh_data(key: str, fetch_func):
    """刷新单个数据项（带锁，防止并发刷新）"""
    cache = _cache[key]
    if cache["loading"]:
        return  # 已经在刷新了

    cache["loading"] = True
    try:
        data = fetch_func()
        if data:
            cache["data"] = data
            cache["time"] = time.time()
            print(f"[缓存] {key} 刷新成功, {time.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"[缓存] {key} 刷新失败: {e}")
    finally:
        cache["loading"] = False


def _get_cached_data(key: str, fetch_func):
    """获取缓存数据，如果缓存过期则触发刷新（异步）"""
    cache = _cache[key]
    now = time.time()

    # 有缓存且未过期，直接返回
    if cache["data"] is not None and (now - cache["time"]) < REFRESH_INTERVAL[key]:
        return cache["data"]

    # 没有任何缓存（第一次请求）：同步加载，确保有数据再返回
    if cache["data"] is None:
        if not cache["loading"]:
            _refresh_data(key, fetch_func)
        else:
            # 正在加载中，等待完成（简单轮询）
            for _ in range(600):  # 最多等 60 秒
                time.sleep(0.1)
                if not cache["loading"]:
                    break
        return cache["data"]

    # 有旧缓存但已过期：先返回旧数据，后台异步刷新
    if not cache["loading"]:
        def _async_refresh():
            _refresh_data(key, fetch_func)
        t = threading.Thread(target=_async_refresh, daemon=True)
        t.start()

    return cache["data"]


def get_industry_boards_cached() -> Optional[List[BoardInfo]]:
    """获取行业板块（缓存版）"""
    return _get_cached_data("industry_boards", board_data.get_industry_boards)


def get_concept_boards_cached() -> Optional[List[BoardInfo]]:
    """获取概念板块（缓存版）"""
    return _get_cached_data("concept_boards", board_data.get_concept_boards)


def get_market_summary_cached() -> Optional[MarketSummary]:
    """获取市场概览（缓存版）"""
    return _get_cached_data("market_summary", market_data.get_market_summary)


def start_cache_refresh():
    """启动后台定时刷新线程（启动时调用一次）"""
    global _refresh_thread

    def _refresh_loop():
        print("[缓存] 后台定时刷新已启动")
        # 启动时先刷新一遍
        _refresh_data("market_summary", market_data.get_market_summary)
        _refresh_data("industry_boards", board_data.get_industry_boards)
        _refresh_data("concept_boards", board_data.get_concept_boards)

        # 定时循环刷新
        while not _stop_flag.is_set():
            time.sleep(10)  # 每 10 秒检查一次是否需要刷新
            now = time.time()

            for key, interval in REFRESH_INTERVAL.items():
                cache = _cache[key]
                if cache["data"] and (now - cache["time"]) >= interval:
                    funcs = {
                        "industry_boards": board_data.get_industry_boards,
                        "concept_boards": board_data.get_concept_boards,
                        "market_summary": market_data.get_market_summary,
                    }
                    _refresh_data(key, funcs[key])

    if _refresh_thread is None:
        _refresh_thread = threading.Thread(target=_refresh_loop, daemon=True)
        _refresh_thread.start()


def stop_cache_refresh():
    """停止后台刷新（关闭服务时调用）"""
    _stop_flag.set()
