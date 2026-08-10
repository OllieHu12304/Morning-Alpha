"""測試 TechNews adapter 輸出的共同新聞格式。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from technews_adapter import parse_articles  # noqa: E402


TECHNEWS_HTML = """
<article class="post">
  <h1 class="entry-title">
    <a href="https://technews.tw/example/">測試科技新聞</a>
  </h1>
  <span class="head">發布日期</span>
  <span class="body">2026 年 08 月 11 日 09:30</span>
</article>
"""


class TechNewsAdapterTests(unittest.TestCase):
    def test_parse_articles_returns_common_news_record(self):
        articles = parse_articles(TECHNEWS_HTML)

        self.assertEqual(articles, [{
            "source": "technews",
            "source_category": None,
            "title": "測試科技新聞",
            "publish_time": datetime(2026, 8, 11, 9, 30),
            "url": "https://technews.tw/example/",
        }])

    def test_parse_articles_skips_incomplete_article(self):
        html = '<article class="post"><h1>缺少必要欄位</h1></article>'

        with self.assertRaisesRegex(ValueError, "沒有可用文章"):
            parse_articles(html)

    def test_parse_articles_detects_missing_article_structure(self):
        with self.assertRaisesRegex(ValueError, "article.post"):
            parse_articles("<html><body>新版首頁</body></html>")


if __name__ == "__main__":
    unittest.main()
