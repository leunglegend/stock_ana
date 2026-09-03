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


def _run_sync(awaitable):
    import asyncio
    return asyncio.run(awaitable)


if __name__ == "__main__":
    unittest.main()
