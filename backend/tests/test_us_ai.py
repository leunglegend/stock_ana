import unittest

from app.services import ai_analyst
from app.services.ai_analyst import US_MARKET_SYSTEM_PROMPT, _build_us_market_prompt
from app.models.schemas import UsSector


def _snap():
    class S:
        as_of = "2026-09-02"
        indices = []
        sectors = [UsSector(name="信息技术", change_pct=2.0, leading_symbol="NVDA",
                            leading_name="NVIDIA", leading_change_pct=5.0,
                            advancers=2, decliners=1, constituent_count=3),
                   UsSector(name="能源", change_pct=-1.5, leading_symbol="XOM",
                            leading_change_pct=-3.0, advancers=0, decliners=2,
                            constituent_count=2)]
    return S()


def _sectors_snap(*sectors):
    """构造一个只带 sectors 的极简快照（板块按 change_pct 降序，与上游一致）。"""
    ordered = sorted(sectors, key=lambda s: s.change_pct, reverse=True)

    class S:
        as_of = "2026-09-02"
        indices = []
        sectors = ordered

    return S()


def _us_sector(name, pct, symbol):
    return UsSector(name=name, change_pct=pct, leading_symbol=symbol,
                    leading_name=symbol, leading_change_pct=pct,
                    advancers=int(pct > 0), decliners=int(pct < 0),
                    constituent_count=1)


class UsAiTest(unittest.TestCase):
    def test_system_prompt_bans_attribution_and_requires_fallback(self):
        text = US_MARKET_SYSTEM_PROMPT
        for bad in ("由于", "受", "影响", "因为", "因此", "导致"):
            self.assertIn(bad, text)   # 禁令以"不得使用 XX"形式出现，故禁令词本身在 prompt 中
        self.assertIn("标普500", text)

    def test_prompt_injects_verifiable_numbers(self):
        prompt = _build_us_market_prompt(_snap())
        self.assertIn("信息技术", prompt)
        self.assertIn("+2.00%", prompt)
        self.assertIn("NVDA", prompt)
        self.assertIn("2026-09-02", prompt)

    def test_ai_unavailable_returns_static_guard(self):
        async def run():
            out = []
            # ai_available 是 Settings 上的只读 @property，需在类层级替换描述符才能置 False
            with unittest.mock.patch.object(type(ai_analyst.settings), "ai_available", False):
                async for chunk in ai_analyst.analyze_us_market_stream(_snap()):
                    out.append(chunk)
            return "".join(out)

        text = _run_sync(run())
        self.assertIn("AI 服务暂不可用", text)

    def test_fallback_sentence_on_insufficient_data(self):
        prompt = _build_us_market_prompt(None)
        self.assertIn("主线暂不明朗", prompt)

    def test_all_negative_day_lists_no_gainer(self):
        # 全绿下跌日：领涨板块必须为「无」，不得把下跌板块标成领涨（与 /summary 口径一致）
        snap = _sectors_snap(
            _us_sector("能源", -0.4, "XOM"),
            _us_sector("信息技术", -1.5, "NVDA"),
            _us_sector("金融", -2.2, "JPM"),
        )
        prompt = _build_us_market_prompt(snap)
        gainer_line = next(line for line in prompt.splitlines()
                           if line.startswith("【领涨板块】"))
        self.assertEqual(gainer_line, "【领涨板块】无")
        # 领跌侧仍应列出最弱的板块（升序：最跌在前）
        self.assertIn("【领跌板块】金融 -2.20%", prompt)
        # 全绿日不存在任何带正负号标成「领涨 X」的成分行
        for line in prompt.splitlines():
            self.assertNotIn("（领涨", line)

    def test_all_positive_day_lists_no_loser(self):
        # 全红上涨日：领跌板块必须为「无」，不得把上涨板块标成领跌
        snap = _sectors_snap(
            _us_sector("信息技术", 1.2, "NVDA"),
            _us_sector("能源", 2.5, "XOM"),
        )
        prompt = _build_us_market_prompt(snap)
        loser_line = next(line for line in prompt.splitlines()
                          if line.startswith("【领跌板块】"))
        self.assertEqual(loser_line, "【领跌板块】无")
        self.assertIn("【领涨板块】能源 +2.50%", prompt)
        for line in prompt.splitlines():
            self.assertNotIn("（领跌", line)


def _run_sync(awaitable):
    import asyncio
    return asyncio.run(awaitable)


if __name__ == "__main__":
    unittest.main()
