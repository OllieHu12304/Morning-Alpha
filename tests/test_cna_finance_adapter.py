"""測試中央社財經 RSS adapter。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "cna_finance.xml"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from cna_finance_adapter import parse_articles  # noqa: E402


class CnaFinanceAdapterTests(unittest.TestCase):
    def test_parse_articles_returns_common_news_record(self):
        xml_text = FIXTURE_PATH.read_text(encoding="utf-8")
        articles = parse_articles(xml_text)

        self.assertEqual(articles[0], {
            "source": "cna",
            "source_category": "產經證券",
            "title": "測試財經新聞一",
            "publish_time": datetime(2026, 8, 11, 9, 30),
            "url": "https://www.cna.com.tw/news/afe/202608110001.aspx",
        })
        self.assertEqual(len(articles), 2)
        self.assertNotIn(
            "今彩539第115193期　頭獎1注中獎",
            [article["title"] for article in articles],
        )
        self.assertNotIn(
            "威力彩第115064期 頭獎槓龜",
            [article["title"] for article in articles],
        )

    def test_parse_articles_skips_item_with_missing_fields(self):
        xml_text = """
        <rss><channel><item><title>缺少網址</title></item></channel></rss>
        """

        with self.assertRaisesRegex(ValueError, "沒有可用文章"):
            parse_articles(xml_text)

    def test_parse_articles_detects_missing_item_structure(self):
        with self.assertRaisesRegex(ValueError, "找不到 item"):
            parse_articles("<rss><channel></channel></rss>")

    def test_parse_articles_rejects_invalid_xml(self):
        with self.assertRaisesRegex(ValueError, "XML"):
            parse_articles("<rss>")


if __name__ == "__main__":
    unittest.main()
