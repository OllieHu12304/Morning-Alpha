"""測試追蹤公司個人化晨報。"""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from personalized_brief import (  # noqa: E402
    build_personalized_brief,
    build_related_news_records,
)


def make_watchlist():
    return [{
        "company_id": 8,
        "name": "台灣積體電路製造股份有限公司",
        "short_name": "台積電",
        "ticker": "2330",
    }]


class PersonalizedBriefTests(unittest.TestCase):
    def test_related_news_merges_multiple_watched_companies(self):
        columns = [
            "id",
            "source",
            "publisher",
            "source_article_id",
            "source_category",
            "analysis_category",
            "title",
            "publish_time",
            "url",
            "company_id",
            "company_name",
            "short_name",
            "ticker",
        ]
        shared_news = [
            1,
            "cna",
            "cna",
            "example-1",
            "產經證券",
            "半導體",
            "兩家公司合作測試新聞",
            datetime(2026, 8, 11, 10, 0),
            "https://example.com/1",
        ]
        rows = [
            (*shared_news, 8, "台積電公司", "台積電", "2330"),
            (*shared_news, 9, "聯發科技公司", "聯發科", "2454"),
        ]

        records = build_related_news_records(rows, columns)

        self.assertEqual(len(records), 1)
        self.assertEqual(len(records[0]["companies"]), 2)

    def test_build_brief_includes_recent_news_outside_daily_window(self):
        records = [{
            "id": 1,
            "source": "cna",
            "publisher": "cna",
            "source_article_id": "example-1",
            "source_category": "產經證券",
            "analysis_category": "半導體",
            "title": "台積電測試新聞",
            "publish_time": "2026-08-12T10:00:00",
            "url": "https://example.com/1",
            "companies": make_watchlist(),
        }]

        brief = build_personalized_brief(
            records,
            date(2026, 8, 12),
            make_watchlist(),
        )

        self.assertEqual(brief["watchlist_count"], 1)
        self.assertEqual(brief["article_count"], 1)
        self.assertIn("1 篇近期相關新聞", brief["summary"])
        self.assertEqual(brief["highlights"][0]["companies"][0]["ticker"], "2330")
        self.assertTrue(any("標題規則" in item for item in brief["limitations"]))

    def test_build_brief_keeps_latest_five_news_per_company(self):
        records = []

        for index in range(7):
            records.append({
                "id": index + 1,
                "source": "cna",
                "publisher": "cna",
                "source_article_id": f"example-{index + 1}",
                "source_category": "產經證券",
                "analysis_category": "半導體",
                "title": f"台積電測試新聞 {index + 1}",
                "publish_time": f"2026-08-{index + 1:02d}T10:00:00",
                "url": f"https://example.com/{index + 1}",
                "companies": make_watchlist(),
            })

        brief = build_personalized_brief(
            records,
            date(2026, 8, 12),
            make_watchlist(),
        )

        self.assertEqual(brief["article_count"], 5)
        self.assertEqual(len(brief["highlights"]), 5)
        self.assertNotIn(
            "台積電測試新聞 1",
            [item["title"] for item in brief["highlights"]],
        )

    def test_empty_watchlist_explains_how_to_start(self):
        brief = build_personalized_brief([], date(2026, 8, 12), [])

        self.assertEqual(brief["article_count"], 0)
        self.assertIn("尚未加入追蹤公司", brief["summary"])
        self.assertIn("搜尋公司", brief["summary"])


if __name__ == "__main__":
    unittest.main()
