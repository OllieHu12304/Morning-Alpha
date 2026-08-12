"""測試 Dashboard 每個取得來源最新 60 篇的平衡樣本。"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SOURCE_DIRECTORY))

from read_news import get_balanced_recent_news  # noqa: E402


class BalancedNewsTests(unittest.TestCase):
    def create_dataframe(self):
        records = []
        base_time = datetime(2026, 8, 12, 12, 0)

        for source, count in [("twse_disclosure", 75), ("cna", 15)]:
            for index in range(count):
                records.append({
                    "source": source,
                    "publish_time": base_time - timedelta(minutes=index),
                    "title": f"{source}-{index}",
                })

        return pd.DataFrame(records)

    def test_keeps_latest_sixty_from_each_available_source(self):
        balanced = get_balanced_recent_news(self.create_dataframe())

        source_counts = balanced["source"].value_counts().to_dict()
        self.assertEqual(source_counts, {
            "twse_disclosure": 60,
            "cna": 15,
        })
        self.assertIn("twse_disclosure-59", balanced["title"].tolist())
        self.assertNotIn("twse_disclosure-60", balanced["title"].tolist())

    def test_combined_result_is_sorted_by_latest_publish_time(self):
        balanced = get_balanced_recent_news(self.create_dataframe())

        self.assertTrue(balanced["publish_time"].is_monotonic_decreasing)

    def test_does_not_modify_complete_database_dataframe(self):
        dataframe = self.create_dataframe()

        get_balanced_recent_news(dataframe)

        self.assertEqual(len(dataframe), 90)

    def test_rejects_invalid_source_limit(self):
        with self.assertRaisesRegex(ValueError, "正整數"):
            get_balanced_recent_news(self.create_dataframe(), 0)

    def test_dashboard_explains_latest_sixty_policy(self):
        html = (PROJECT_DIRECTORY / "dashboard" / "index.html").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "每個取得來源最多採用發布時間最新的 60 篇",
            html,
        )


if __name__ == "__main__":
    unittest.main()
