import unittest

from app.services.sse import format_sse_data


def decode_sse_data(payload: str) -> str:
    lines = payload.removesuffix("\n\n").split("\n")
    values = [line.removeprefix("data: ") for line in lines if line.startswith("data: ")]
    return "\n".join(values)


class SseFormattingTest(unittest.TestCase):
    def test_multiline_model_chunks_round_trip_without_losing_newlines(self):
        for chunk in ["正文", "\n", "\n\n", "标题\n正文", "第一段\n\n第二段"]:
            with self.subTest(chunk=repr(chunk)):
                self.assertEqual(chunk, decode_sse_data(format_sse_data(chunk)))


if __name__ == "__main__":
    unittest.main()
