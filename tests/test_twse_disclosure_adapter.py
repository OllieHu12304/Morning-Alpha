"""使用固定 fixture 測試 TWSE 重大訊息 adapter。"""

from datetime import datetime
import sys
import unittest
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
FIXTURE_PATH = (
    PROJECT_DIRECTORY / "tests" / "fixtures" / "twse_disclosures.json"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from twse_disclosure_adapter import (  # noqa: E402
    build_mops_url,
    parse_disclosures,
    parse_publish_time,
)


class TwseDisclosureAdapterTests(unittest.TestCase):
    def test_parse_disclosures_returns_common_news_records(self):
        articles = parse_disclosures(
            FIXTURE_PATH.read_text(encoding="utf-8")
        )

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["source"], "twse_disclosure")
        self.assertEqual(articles[0]["publisher"], "twse")
        self.assertEqual(len(articles[0]["source_article_id"]), 16)
        self.assertEqual(articles[0]["source_category"], "官方重大訊息")
        self.assertEqual(
            articles[0]["title"],
            "2327 國巨｜公告本公司董事會決議事項",
        )
        self.assertEqual(
            articles[0]["publish_time"],
            datetime(2026, 8, 11, 15, 30, 45),
        )
        self.assertIn("co_id=2327", articles[0]["url"])
        self.assertIn("spoke_time=153045", articles[0]["url"])

    def test_parse_publish_time_accepts_five_digit_time(self):
        self.assertEqual(
            parse_publish_time("1150811", "70003"),
            datetime(2026, 8, 11, 7, 0, 3),
        )

    def test_build_mops_url_is_unique_for_publish_time(self):
        first_url = build_mops_url(
            "2327",
            datetime(2026, 8, 11, 9, 0),
            "第一則公告",
        )
        second_url = build_mops_url(
            "2327",
            datetime(2026, 8, 11, 9, 0),
            "第二則公告",
        )

        self.assertNotEqual(first_url, second_url)

    def test_parse_disclosures_rejects_invalid_json(self):
        with self.assertRaisesRegex(ValueError, "有效 JSON"):
            parse_disclosures("not-json")

    def test_parse_disclosures_rejects_empty_list(self):
        with self.assertRaisesRegex(ValueError, "非空 list"):
            parse_disclosures("[]")


if __name__ == "__main__":
    unittest.main()
