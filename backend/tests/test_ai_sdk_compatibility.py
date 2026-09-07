import ast
import inspect
import unittest
from pathlib import Path

from anthropic.resources.messages import AsyncMessages, Messages

from app.services.ai_analyst import _build_market_summary_prompt


AI_ANALYST_PATH = Path(__file__).parents[1] / "app" / "services" / "ai_analyst.py"


class AiSdkCompatibilityTest(unittest.TestCase):
    def test_market_prompt_expresses_turnover_in_consistent_units(self):
        prompt = _build_market_summary_prompt(
            3952.18, -0.11, -4.39,
            13953.07, -0.68, -95.81,
            3424.4, -1.41, -48.95,
            3013, 2390, 82, 1, 21177.33,
            [], [],
        )

        self.assertIn("21,177 亿元（约 2.12 万亿元）", prompt)
        self.assertIn("不得写成 21,177 万亿元", prompt)

    def test_ai_calls_only_use_parameters_supported_by_installed_sdk(self):
        tree = ast.parse(AI_ANALYST_PATH.read_text(encoding="utf-8"))
        async_parameters = set(inspect.signature(AsyncMessages.create).parameters)
        sync_parameters = set(inspect.signature(Messages.create).parameters)

        checked_calls = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"stream", "create"}:
                continue
            owner = node.func.value
            if not isinstance(owner, ast.Attribute) or owner.attr != "messages":
                continue

            supported = async_parameters if node.func.attr == "stream" else sync_parameters
            unsupported = {keyword.arg for keyword in node.keywords if keyword.arg} - supported
            self.assertEqual(set(), unsupported, f"unsupported parameters in {node.func.attr}")
            checked_calls += 1

        self.assertEqual(7, checked_calls)


if __name__ == "__main__":
    unittest.main()
