import asyncio
import threading
import unittest
from unittest.mock import patch

from app.routes.board import get_board_stocks


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


if __name__ == "__main__":
    unittest.main()
