"""測試規則式結構化每日晨報。"""

import sys
import unittest
from datetime import date
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from daily_brief import build_daily_brief, select_brief_records  # noqa: E402


def make_record(title, publish_time, source="cna", category="財經"):
    """建立晨報 tests 使用的最小新聞 record。"""
    slug = title.replace(" ", "-")
    return {
        "source": source,
        "source_category": "產經證券" if source == "cna" else None,
        "analysis_category": category,
        "title": title,
        "publish_time": publish_time,
        "url": f"https://example.com/{slug}",
    }


class DailyBriefTests(unittest.TestCase):
    def test_select_records_uses_inclusive_start_and_exclusive_end(self):
        records = [
            make_record("開始邊界", "2026-08-11T07:00:00"),
            make_record("結束邊界", "2026-08-12T07:00:00"),
            make_record("時間窗之前", "2026-08-11T06:59:59"),
        ]

        selected = select_brief_records(records, date(2026, 8, 12))

        self.assertEqual(
            [record["title"] for record in selected],
            ["開始邊界"],
        )

    def test_build_brief_returns_structured_statistics_and_limits(self):
        records = [
            make_record(
                "台積電 人工智慧 晶片成長",
                "2026-08-11T10:00:00",
                category="半導體",
            ),
            make_record(
                "台積電 人工智慧 晶片需求",
                "2026-08-11T10:30:00",
                category="半導體",
            ),
            make_record(
                "市場交易整理",
                "2026-08-11T11:00:00",
                source="technews",
            ),
        ]

        brief = build_daily_brief(records, date(2026, 8, 12))

        self.assertEqual(brief["brief_date"], "2026-08-12")
        self.assertEqual(brief["article_count"], 3)
        self.assertEqual(brief["sources"][0], {
            "name": "中央通訊社",
            "count": 2,
        })
        self.assertEqual(brief["categories"][0], {
            "name": "半導體",
            "count": 2,
        })
        self.assertLessEqual(len(brief["keywords"]), 5)
        self.assertEqual(len(brief["highlights"]), 3)
        self.assertIn("本期共收錄 3 篇新聞", brief["summary"])
        self.assertIn("不構成投資建議", brief["limitations"][-1])

    def test_highlight_explains_event_group_selection(self):
        records = [
            make_record(
                "台積電 人工智慧 晶片成長",
                "2026-08-11T10:00:00",
                category="半導體",
            ),
            make_record(
                "台積電 人工智慧 晶片需求",
                "2026-08-11T10:30:00",
                category="半導體",
            ),
        ]

        brief = build_daily_brief(records, date(2026, 8, 12))

        self.assertEqual(brief["highlights"][0]["event_group_size"], 2)
        self.assertEqual(
            brief["highlights"][0]["selection_reason"],
            "同事件共有 2 篇報導",
        )

    def test_empty_window_returns_clear_summary(self):
        brief = build_daily_brief([], date(2026, 8, 12))

        self.assertEqual(brief["article_count"], 0)
        self.assertEqual(brief["summary"], "本期時間窗內沒有可用新聞。")
        self.assertEqual(brief["highlights"], [])


if __name__ == "__main__":
    unittest.main()
