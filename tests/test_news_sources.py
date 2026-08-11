"""測試多個新聞來源的合併流程。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import news_sources  # noqa: E402


class NewsSourcesTests(unittest.TestCase):
    def test_fetch_all_articles_keeps_records_from_every_source(self):
        technews_articles = [{"source": "technews"}]
        cna_articles = [{"source": "cna"}]
        disclosure_articles = [{"source": "twse_disclosure"}]

        with patch.object(
            news_sources,
            "fetch_technews",
            return_value=technews_articles,
        ), patch.object(
            news_sources,
            "fetch_cna_finance",
            return_value=cna_articles,
        ), patch.object(
            news_sources,
            "fetch_twse_disclosures",
            return_value=disclosure_articles,
        ):
            articles = news_sources.fetch_all_articles()

        self.assertEqual(
            articles,
            technews_articles + cna_articles + disclosure_articles,
        )

    def test_source_failure_does_not_discard_successful_source(self):
        cna_articles = [{"source": "cna"}]

        with patch.object(
            news_sources,
            "fetch_technews",
            side_effect=requests.Timeout("TechNews timeout"),
        ), patch.object(
            news_sources,
            "fetch_cna_finance",
            return_value=cna_articles,
        ), patch.object(
            news_sources,
            "fetch_twse_disclosures",
            return_value=[],
        ):
            articles, source_results = (
                news_sources.fetch_all_articles_with_status()
            )

        self.assertEqual(articles, cna_articles)
        self.assertEqual(source_results[0]["source"], "technews")
        self.assertEqual(source_results[0]["status"], "failure")
        self.assertEqual(source_results[1]["source"], "cna")
        self.assertEqual(source_results[1]["status"], "success")
        self.assertEqual(source_results[1]["article_count"], 1)

    def test_structure_failure_does_not_stop_other_source(self):
        technews_articles = [{"source": "technews"}]

        with patch.object(
            news_sources,
            "fetch_technews",
            return_value=technews_articles,
        ), patch.object(
            news_sources,
            "fetch_cna_finance",
            side_effect=ValueError("RSS 結構異常"),
        ), patch.object(
            news_sources,
            "fetch_twse_disclosures",
            return_value=[],
        ):
            articles, source_results = (
                news_sources.fetch_all_articles_with_status()
            )

        self.assertEqual(articles, technews_articles)
        self.assertEqual(source_results[0]["status"], "success")
        self.assertEqual(source_results[1]["status"], "failure")
        self.assertEqual(source_results[1]["error_message"], "RSS 結構異常")

    def test_all_sources_failure_stops_collection(self):
        with patch.object(
            news_sources,
            "fetch_technews",
            side_effect=requests.HTTPError("503"),
        ), patch.object(
            news_sources,
            "fetch_cna_finance",
            side_effect=requests.Timeout("RSS timeout"),
        ), patch.object(
            news_sources,
            "fetch_twse_disclosures",
            side_effect=requests.HTTPError("TWSE 503"),
        ):
            with self.assertRaisesRegex(ValueError, "所有新聞來源都失敗"):
                news_sources.fetch_all_articles()


if __name__ == "__main__":
    unittest.main()
