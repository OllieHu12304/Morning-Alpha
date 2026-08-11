"""測試跨來源相似新聞事件分組。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from event_grouping import (  # noqa: E402
    SAME_TITLE_REASON,
    SIMILAR_EVENT_REASON,
    calculate_similarity,
    group_similar_events,
    has_same_normalized_title,
    identify_article_relationship,
    is_similar_event,
    normalize_title,
)


class EventGroupingTests(unittest.TestCase):
    def create_article(self, source, title, publish_time):
        return {
            "source": source,
            "title": title,
            "publish_time": publish_time,
            "url": f"https://example.com/{source}",
        }

    def test_calculate_similarity_uses_jaccard_formula(self):
        similarity = calculate_similarity(
            {"台積電", "晶片", "營收"},
            {"台積電", "晶片", "投資"},
        )

        self.assertEqual(similarity, 0.5)

    def test_normalize_title_removes_formatting_differences(self):
        first_title = "中華電攜手 Nokia：推動 AI-RAN"
        second_title = "中華電攜手ＮＯＫＩＡ 推動 ai-ran"

        self.assertEqual(
            normalize_title(first_title),
            normalize_title(second_title),
        )

    def test_same_normalized_title_is_detected(self):
        first_article = self.create_article(
            "cna",
            "國巨：公布七月營收",
            "2026-08-11T09:00:00",
        )
        second_article = self.create_article(
            "another_source",
            "國巨 公布七月營收",
            "2026-08-11T10:00:00",
        )

        self.assertTrue(
            has_same_normalized_title(first_article, second_article)
        )
        self.assertEqual(
            identify_article_relationship(first_article, second_article),
            SAME_TITLE_REASON,
        )

    def test_same_title_outside_time_window_is_not_grouped(self):
        first_article = self.create_article(
            "cna",
            "國巨公布營收",
            "2026-08-01T09:00:00",
        )
        second_article = self.create_article(
            "another_source",
            "國巨公布營收",
            "2026-08-11T09:00:00",
        )

        self.assertIsNone(
            identify_article_relationship(first_article, second_article)
        )

    def test_group_similar_events_groups_but_keeps_every_article(self):
        records = [
            self.create_article(
                "cna",
                "台積電第二季營收創新高 AI 晶片需求成長",
                "2026-08-11T09:30:00",
            ),
            self.create_article(
                "technews",
                "AI 晶片需求帶動 台積電第二季營收創新高",
                "2026-08-11T10:00:00",
            ),
            self.create_article(
                "cna",
                "太空望遠鏡觀測遙遠星系",
                "2026-08-11T11:00:00",
            ),
        ]

        grouped_records = group_similar_events(records)

        self.assertEqual(len(grouped_records), 3)
        self.assertIsNotNone(grouped_records[0]["event_group_id"])
        self.assertEqual(
            grouped_records[0]["event_group_id"],
            grouped_records[1]["event_group_id"],
        )
        self.assertEqual(grouped_records[0]["event_group_size"], 2)
        self.assertEqual(
            grouped_records[0]["event_group_reason"],
            SIMILAR_EVENT_REASON,
        )
        self.assertIsNone(grouped_records[2]["event_group_id"])

    def test_same_title_groups_articles_without_deleting_them(self):
        records = [
            self.create_article(
                "cna",
                "國巨：公布營收",
                "2026-08-11T09:00:00",
            ),
            self.create_article(
                "another_source",
                "國巨 公布營收",
                "2026-08-11T10:00:00",
            ),
        ]

        grouped_records = group_similar_events(records)

        self.assertEqual(len(grouped_records), 2)
        self.assertEqual(
            grouped_records[0]["event_group_id"],
            grouped_records[1]["event_group_id"],
        )
        self.assertEqual(
            grouped_records[0]["event_group_reason"],
            SAME_TITLE_REASON,
        )

    def test_articles_outside_time_window_are_not_grouped(self):
        first_article = self.create_article(
            "cna",
            "台積電營收創新高 晶片需求成長",
            "2026-08-01T09:00:00",
        )
        second_article = self.create_article(
            "technews",
            "台積電營收創新高 晶片需求成長",
            "2026-08-10T09:00:00",
        )

        self.assertFalse(is_similar_event(first_article, second_article))

    def test_group_id_is_stable_for_same_records(self):
        records = [
            self.create_article(
                "cna",
                "台積電營收創新高 晶片需求成長",
                "2026-08-11T09:00:00",
            ),
            self.create_article(
                "technews",
                "晶片需求成長 台積電營收創新高",
                "2026-08-11T10:00:00",
            ),
        ]

        first_result = group_similar_events(records)
        second_result = group_similar_events(records)

        self.assertEqual(
            first_result[0]["event_group_id"],
            second_result[0]["event_group_id"],
        )


if __name__ == "__main__":
    unittest.main()
