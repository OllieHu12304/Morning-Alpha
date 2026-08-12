"""測試多來源新聞共同資料格式。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from news_record import create_news_record, validate_news_record  # noqa: E402


class NewsRecordTests(unittest.TestCase):
    def test_create_news_record_returns_common_fields(self):
        publish_time = datetime(2026, 8, 11, 9, 30)

        record = create_news_record(
            source=" technews ",
            publisher=" technews ",
            source_article_id=" article-123 ",
            source_category=" 科技 ",
            title=" 測試新聞 ",
            publish_time=publish_time,
            url=" https://technews.tw/example/ ",
        )

        self.assertEqual(record, {
            "source": "technews",
            "publisher": "technews",
            "source_article_id": "article-123",
            "source_category": "科技",
            "title": "測試新聞",
            "publish_time": publish_time,
            "url": "https://technews.tw/example/",
        })

    def test_create_news_record_allows_missing_source_category(self):
        record = create_news_record(
            source="cna",
            publisher="cna",
            source_article_id=None,
            source_category=None,
            title="測試新聞",
            publish_time=datetime(2026, 8, 11, 9, 30),
            url="https://www.cna.com.tw/news/example.aspx",
        )

        self.assertIsNone(record["source_category"])

    def test_validate_news_record_reports_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "source_category"):
            validate_news_record({
                "source": "technews",
                "publisher": "technews",
                "source_article_id": None,
                "title": "測試新聞",
                "publish_time": datetime(2026, 8, 11, 9, 30),
                "url": "https://technews.tw/example/",
            })

    def test_create_news_record_rejects_non_datetime_publish_time(self):
        with self.assertRaisesRegex(ValueError, "datetime"):
            create_news_record(
                source="technews",
                publisher="technews",
                source_article_id=None,
                source_category="科技",
                title="測試新聞",
                publish_time="2026-08-11 09:30",
                url="https://technews.tw/example/",
            )

    def test_create_news_record_rejects_empty_required_text(self):
        with self.assertRaisesRegex(ValueError, "title"):
            create_news_record(
                source="technews",
                publisher="technews",
                source_article_id=None,
                source_category="科技",
                title="   ",
                publish_time=datetime(2026, 8, 11, 9, 30),
                url="https://technews.tw/example/",
            )

    def test_create_news_record_defaults_publisher_to_source(self):
        record = create_news_record(
            source="technews",
            source_category=None,
            title="測試新聞",
            publish_time=datetime(2026, 8, 11, 9, 30),
            url="https://technews.tw/example/",
        )

        self.assertEqual(record["publisher"], "technews")
        self.assertIsNone(record["source_article_id"])


if __name__ == "__main__":
    unittest.main()
