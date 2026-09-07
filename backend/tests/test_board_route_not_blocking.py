import asyncio
import threading
import unittest
from unittest.mock import patch

from app.routes.board import (
    get_board_stocks,
    get_concept_boards,
    get_industry_boards,
    get_market_summary,
)


class BoardRouteNotBlockingTest(unittest.IsolatedAsyncioTestCase):
    async def test_board_stocks_call_runs_in_worker_thread(self):
        """板块成分股同步抓取必须经 run_in_threadpool，不能占用事件循环线程。"""
        loop_thread_id = threading.get_ident()
        calls = []

        def slow_sync_fetch(_board_name, _board_type):
            calls.append(threading.get_ident())
            return [object()]

        with patch("app.routes.board.board_data.get_board_stocks", side_effect=slow_sync_fetch):
            result = await get_board_stocks("industry", "半导体")

        self.assertEqual(1, len(result))
        self.assertEqual(1, len(calls))
        self.assertNotEqual(loop_thread_id, calls[0], "同步数据抓取阻塞了事件循环线程")

    async def test_industry_cached_fetch_runs_in_worker_thread(self):
        """板块列表冷启动的同步缓存等待也必须经线程池。"""
        loop_thread_id = threading.get_ident()
        calls = []

        def slow_cached_fetch():
            calls.append(threading.get_ident())
            return [object()]

        with patch(
            "app.routes.board.get_industry_boards_cached",
            side_effect=slow_cached_fetch,
        ):
            result = await get_industry_boards()

        self.assertEqual(1, len(result))
        self.assertNotEqual(loop_thread_id, calls[0], "板块列表冷加载阻塞了事件循环线程")

    async def test_concept_cached_fetch_runs_in_worker_thread(self):
        """概念板块冷启动的同步缓存等待也必须经线程池。"""
        loop_thread_id = threading.get_ident()
        calls = []

        def slow_cached_fetch():
            calls.append(threading.get_ident())
            return [object()]

        with patch(
            "app.routes.board.get_concept_boards_cached",
            side_effect=slow_cached_fetch,
        ):
            result = await get_concept_boards()

        self.assertEqual(1, len(result))
        self.assertNotEqual(loop_thread_id, calls[0], "概念板块冷加载阻塞了事件循环线程")

    async def test_market_summary_cached_fetch_runs_in_worker_thread(self):
        """市场概览冷启动的同步缓存等待也必须经线程池。"""
        loop_thread_id = threading.get_ident()
        calls = []

        def slow_cached_fetch():
            calls.append(threading.get_ident())
            return object()

        with patch(
            "app.routes.board.get_market_summary_cached",
            side_effect=slow_cached_fetch,
        ):
            result = await get_market_summary()

        self.assertIsNotNone(result)
        self.assertNotEqual(loop_thread_id, calls[0], "市场概览冷加载阻塞了事件循环线程")


if __name__ == "__main__":
    unittest.main()
