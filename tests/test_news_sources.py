"""測試多個新聞來源的合併流程。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import news_sources  # noqa: E402


class NewsSourcesTests(unittest.TestCase):
    def test_fetch_all_articles_keeps_records_from_every_source(self):
        technews_articles = [{"source": "technews"}]
        cna_articles = [{"source": "cna"}]

        with patch.object(
            news_sources,
            "fetch_technews",
            return_value=technews_articles,
        ), patch.object(
            news_sources,
            "fetch_cna_finance",
            return_value=cna_articles,
        ):
            articles = news_sources.fetch_all_articles()

        self.assertEqual(articles, technews_articles + cna_articles)


if __name__ == "__main__":
    unittest.main()
