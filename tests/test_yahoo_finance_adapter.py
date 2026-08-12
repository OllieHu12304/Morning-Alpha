"""使用固定 fixture 測試 Yahoo股市聚合來源 adapter。"""

from datetime import datetime
import sys
import unittest
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
FIXTURE_PATH = (
    PROJECT_DIRECTORY / "tests" / "fixtures" / "yahoo_finance.xml"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from event_grouping import group_similar_events  # noqa: E402
from yahoo_finance_adapter import (  # noqa: E402
    get_source_article_id,
    parse_articles,
    parse_publish_time,
)


class YahooFinanceAdapterTests(unittest.TestCase):
    def test_parse_articles_preserves_aggregator_identity(self):
        articles = parse_articles(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0], {
            "source": "yahoo_tw_finance",
            "publisher": "Yahoo股市",
            "source_article_id": "021600898",
            "source_category": "台股動態",
            "title": "國巨公布七月營收 AI 需求持續成長",
            "publish_time": datetime(2026, 8, 12, 15, 24, 20),
            "url": (
                "https://tw.stock.yahoo.com/news/"
                "yageo-revenue-021600898.html"
            ),
        })

    def test_live_feed_without_source_or_guid_uses_safe_fallbacks(self):
        articles = parse_articles(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(articles[1]["publisher"], "Yahoo股市")
        self.assertEqual(articles[1]["source_article_id"], "071900087")

    def test_guid_text_is_kept_when_it_is_not_a_yahoo_url(self):
        article_id = get_source_article_id(
            "yahoo-article-guid-123",
            "https://tw.stock.yahoo.com/news/example-071900087.html",
        )

        self.assertEqual(article_id, "yahoo-article-guid-123")

    def test_aggregated_article_groups_with_direct_source_without_deletion(self):
        yahoo_article = parse_articles(
            FIXTURE_PATH.read_text(encoding="utf-8")
        )[0]
        yahoo_article["publish_time"] = yahoo_article["publish_time"].isoformat()
        direct_article = {
            "source": "cna",
            "publisher": "cna",
            "source_article_id": "202608110001",
            "source_category": "產經證券",
            "title": "AI 需求持續成長 國巨公布七月營收",
            "publish_time": "2026-08-11T10:05:00",
            "url": "https://www.cna.com.tw/news/afe/202608110001.aspx",
        }

        grouped_articles = group_similar_events([
            direct_article,
            yahoo_article,
        ])

        self.assertEqual(len(grouped_articles), 2)
        self.assertEqual(
            grouped_articles[0]["event_group_id"],
            grouped_articles[1]["event_group_id"],
        )
        self.assertEqual(grouped_articles[0]["event_group_size"], 2)

    def test_parse_publish_time_rejects_invalid_date(self):
        with self.assertRaisesRegex(ValueError, "發布時間"):
            parse_publish_time("不是日期")

    def test_parse_articles_rejects_missing_item_structure(self):
        with self.assertRaisesRegex(ValueError, "找不到 item"):
            parse_articles("<rss><channel></channel></rss>")

    def test_parse_articles_rejects_invalid_xml(self):
        with self.assertRaisesRegex(ValueError, "XML"):
            parse_articles("<rss>")

    def test_parse_articles_rejects_feed_without_usable_articles(self):
        xml_text = """
        <rss><channel><item><title>缺少其他欄位</title></item></channel></rss>
        """

        with self.assertRaisesRegex(ValueError, "沒有可用文章"):
            parse_articles(xml_text)


if __name__ == "__main__":
    unittest.main()
