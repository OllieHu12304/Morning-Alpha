"""使用固定 RSS fixture 測試自由時報財經 adapter。"""

from datetime import datetime
import sys
import unittest
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
FIXTURE_PATH = (
    PROJECT_DIRECTORY / "tests" / "fixtures" / "ltn_business.xml"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from ltn_business_adapter import (  # noqa: E402
    parse_articles,
    parse_publish_time,
)


class LtnBusinessAdapterTests(unittest.TestCase):
    def test_parse_articles_returns_common_news_records(self):
        articles = parse_articles(
            FIXTURE_PATH.read_text(encoding="utf-8")
        )

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0], {
            "source": "ltn",
            "source_category": "財經",
            "title": "國巨公布最新營運消息",
            "publish_time": datetime(2026, 8, 11, 17, 30),
            "url": "https://ec.ltn.com.tw/article/breakingnews/5000001",
        })

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
