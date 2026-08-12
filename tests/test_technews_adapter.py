"""測試 TechNews adapter 輸出的共同新聞格式。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "technews_homepage.html"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from technews_adapter import parse_articles  # noqa: E402


class TechNewsAdapterTests(unittest.TestCase):
    def test_parse_articles_returns_common_news_record(self):
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        articles = parse_articles(html)

        self.assertEqual(articles[0], {
            "source": "technews",
            "publisher": "technews",
            "source_article_id": None,
            "source_category": None,
            "title": "測試科技新聞一",
            "publish_time": datetime(2026, 8, 11, 9, 30),
            "url": "https://technews.tw/example-one/",
        })
        self.assertEqual(len(articles), 6)

    def test_parse_articles_does_not_stop_after_five_articles(self):
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        articles = parse_articles(html)

        self.assertEqual(articles[5]["title"], "測試科技新聞六")
        self.assertEqual(
            articles[5]["url"],
            "https://technews.tw/example-six/",
        )

    def test_parse_articles_skips_incomplete_article(self):
        html = '<article class="post"><h1>缺少必要欄位</h1></article>'

        with self.assertRaisesRegex(ValueError, "沒有可用文章"):
            parse_articles(html)

    def test_parse_articles_detects_missing_article_structure(self):
        with self.assertRaisesRegex(ValueError, "article.post"):
            parse_articles("<html><body>新版首頁</body></html>")


if __name__ == "__main__":
    unittest.main()
