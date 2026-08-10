"""測試 Pandas 新聞整理流程。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from analyze_news import transform_dataframe  # noqa: E402


class AnalyzeNewsTests(unittest.TestCase):
    def test_transform_dataframe_keeps_same_title_with_different_urls(self):
        dataframe = pd.DataFrame([
            {
                "title": "相同標題",
                "publish_time": datetime(2026, 8, 11, 9, 30),
                "url": "https://example.com/one",
            },
            {
                "title": "相同標題",
                "publish_time": datetime(2026, 8, 11, 9, 20),
                "url": "https://example.com/two",
            },
        ])

        result = transform_dataframe(dataframe)

        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["url"], "https://example.com/one")
        self.assertEqual(result.iloc[1]["url"], "https://example.com/two")


if __name__ == "__main__":
    unittest.main()
