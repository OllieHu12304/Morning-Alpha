"""測試 Morning Alpha 統一分析分類。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from news_category import infer_category  # noqa: E402


class NewsCategoryTests(unittest.TestCase):
    def test_infer_category_is_case_insensitive(self):
        self.assertEqual(
            infer_category("Claude 推出生成式 AI 新功能"),
            "AI 與人工智慧",
        )

    def test_infer_category_returns_other_when_no_rule_matches(self):
        self.assertEqual(infer_category("一般新聞標題"), "其他")


if __name__ == "__main__":
    unittest.main()
