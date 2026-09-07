import unittest
from types import SimpleNamespace
from unittest.mock import patch, PropertyMock

from app.services import ai_analyst, report_service


class ReportAiFailureTest(unittest.TestCase):
    def test_completed_report_with_ai_error_text_is_not_usable(self):
        report = SimpleNamespace(
            status="completed",
            error_msg="",
            market_summary="AI 日报总览出错：SDK 参数不兼容",
            stock_reports=[SimpleNamespace(analysis_text="AI 盘后分析出错：SDK 参数不兼容", summary="分析出错")],
        )

        self.assertFalse(report_service.is_report_usable(report))

    def test_completed_report_with_real_content_is_usable(self):
        report = SimpleNamespace(
            status="completed",
            error_msg="",
            market_summary="市场今日震荡运行，成交活跃，板块表现分化。",
            stock_reports=[SimpleNamespace(analysis_text="### 当日表现\n股价震荡。", summary="震荡整理")],
        )

        self.assertTrue(report_service.is_report_usable(report))

    def test_stock_report_ai_exception_is_not_returned_as_normal_content(self):
        client = SimpleNamespace(messages=SimpleNamespace(create=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom"))))
        with patch.object(type(ai_analyst.settings), "ai_available", new_callable=PropertyMock, return_value=True), \
                patch.object(ai_analyst, "_get_sync_client", return_value=client), \
                patch.object(ai_analyst, "_build_stock_daily_prompt", return_value="prompt"):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                ai_analyst.generate_stock_daily_analysis("600519", "贵州茅台", SimpleNamespace(), None)

    def test_report_overview_ai_exception_is_not_returned_as_normal_content(self):
        client = SimpleNamespace(messages=SimpleNamespace(create=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom"))))
        with patch.object(type(ai_analyst.settings), "ai_available", new_callable=PropertyMock, return_value=True), \
                patch.object(ai_analyst, "_get_sync_client", return_value=client):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                ai_analyst.generate_daily_report_overview([], None)


if __name__ == "__main__":
    unittest.main()
