"""測試 Morning Alpha Flask API，不連接正式 MySQL。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pymysql


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import api  # noqa: E402
from pipeline_history import create_pending_step_results  # noqa: E402


def create_test_dataframe():
    """建立 API tests 共用的兩筆假新聞。"""
    return pd.DataFrame([
        {
            "id": 1,
            "source": "technews",
            "publisher": "technews",
            "source_article_id": None,
            "source_category": None,
            "analysis_category": "人工智慧",
            "title": "人工智慧晶片市場持續成長",
            "publish_time": pd.Timestamp("2026-08-11 09:30:00"),
            "url": "https://technews.tw/example-one/",
            "created_at": pd.Timestamp("2026-08-11 09:35:00"),
        },
        {
            "id": 2,
            "source": "cna",
            "publisher": "cna",
            "source_article_id": "1",
            "source_category": "產經證券",
            "analysis_category": "金融市場",
            "title": "金融市場今日交易整理",
            "publish_time": pd.Timestamp("2026-08-11 09:00:00"),
            "url": "https://www.cna.com.tw/news/afe/1.aspx",
            "created_at": pd.Timestamp("2026-08-11 09:05:00"),
        },
    ])


class ApiTests(unittest.TestCase):
    def setUp(self):
        api.app.config["TESTING"] = True
        self.client = api.app.test_client()

    def test_health_returns_ok(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_root_serves_dashboard(self):
        response = self.client.get("/")
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Morning Alpha",
            response.get_data(as_text=True),
        )

    def test_dashboard_javascript_is_served(self):
        response = self.client.get("/app.js")
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'const NEWS_API = "/api/news"',
            response.get_data(as_text=True),
        )

    @patch("api.load_news_company_links")
    @patch("api.load_all_news")
    def test_news_returns_grouped_dashboard_records(
        self,
        mock_load_news,
        mock_load_links,
    ):
        mock_load_news.return_value = create_test_dataframe()
        mock_load_links.return_value = [{
            "news_id": 1,
            "company_id": 8,
            "name": "台灣積體電路製造股份有限公司",
            "short_name": "台積電",
            "industry": "半導體業",
            "ticker": "2330",
            "exchange": "TWSE",
            "matched_text": "台積電",
            "match_method": "alias",
            "confidence": 0.9,
        }]

        response = self.client.get("/api/news")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["news"][0]["source"], "technews")
        self.assertEqual(payload["news"][0]["publisher"], "technews")
        self.assertIsNone(payload["news"][0]["source_article_id"])
        self.assertIn("event_group_id", payload["news"][0])
        self.assertNotIn("id", payload["news"][0])
        self.assertEqual(payload["news"][0]["companies"][0]["ticker"], "2330")
        self.assertEqual(payload["news"][1]["companies"], [])

    @patch("api.load_all_news")
    def test_analytics_returns_charts_keywords_and_time(
        self,
        mock_load_news,
    ):
        mock_load_news.return_value = create_test_dataframe()

        response = self.client.get("/api/analytics")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload["sources"]["labels"],
            ["TechNews 科技新報", "中央通訊社"],
        )
        self.assertEqual(payload["categories"]["values"], [1, 1])
        self.assertTrue(payload["keywords"])
        self.assertEqual(
            payload["last_updated"],
            "2026-08-11T09:35:00",
        )

    @patch("api.load_source_health_events")
    def test_source_health_returns_latest_source_status(self, mock_load_events):
        mock_load_events.return_value = (
            [
                (
                    "technews",
                    "failure",
                    0,
                    "HTTP 503",
                    datetime(2026, 8, 11, 10, 0),
                ),
                (
                    "technews",
                    "success",
                    5,
                    None,
                    datetime(2026, 8, 11, 9, 0),
                ),
            ],
            [
                "source",
                "status",
                "article_count",
                "error_message",
                "attempted_at",
            ],
        )

        response = self.client.get("/api/source-health")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["sources"]), 1)
        self.assertEqual(payload["sources"][0]["status"], "failure")
        self.assertEqual(payload["sources"][0]["error_message"], "HTTP 503")
        self.assertEqual(
            payload["sources"][0]["last_success_at"],
            "2026-08-11T09:00:00+00:00",
        )

    @patch("api.load_pipeline_runs")
    def test_pipeline_runs_returns_recent_execution_history(self, mock_load_runs):
        step_results = create_pending_step_results()
        step_results[0]["status"] = "failure"
        step_results[0]["duration_ms"] = 850
        mock_load_runs.return_value = (
            [(
                9,
                "failure",
                datetime(2026, 8, 11, 10, 0),
                datetime(2026, 8, 11, 10, 0, 1),
                1000,
                "collect_news",
                step_results,
                "HTTP 503",
            )],
            [
                "id",
                "status",
                "started_at",
                "finished_at",
                "duration_ms",
                "failed_step",
                "step_results",
                "error_message",
            ],
        )

        response = self.client.get("/api/pipeline-runs")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["runs"]), 1)
        self.assertEqual(payload["runs"][0]["status"], "failure")
        self.assertEqual(payload["runs"][0]["failed_step"], "collect_news")
        self.assertEqual(payload["runs"][0]["step_results"][0]["status"], "failure")
        mock_load_runs.assert_called_once_with(limit=10)

    @patch("api.load_daily_briefs")
    def test_latest_daily_brief_returns_latest_record(self, mock_load_briefs):
        mock_load_briefs.return_value = [{
            "brief_date": "2026-08-12",
            "article_count": 12,
            "summary": "測試晨報",
        }]

        response = self.client.get("/api/daily-briefs/latest")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["brief"]["brief_date"], "2026-08-12")
        mock_load_briefs.assert_called_once_with(limit=1)

    @patch("api.load_daily_briefs")
    def test_latest_daily_brief_returns_null_when_empty(self, mock_load_briefs):
        mock_load_briefs.return_value = []

        response = self.client.get("/api/daily-briefs/latest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"brief": None})

    @patch("api.load_daily_briefs")
    def test_daily_briefs_returns_history(self, mock_load_briefs):
        mock_load_briefs.return_value = [
            {"brief_date": "2026-08-12"},
            {"brief_date": "2026-08-11"},
        ]

        response = self.client.get("/api/daily-briefs")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["briefs"]), 2)
        mock_load_briefs.assert_called_once_with(limit=30)

    @patch("api.load_daily_briefs")
    def test_daily_brief_hides_database_error_details(self, mock_load_briefs):
        mock_load_briefs.side_effect = pymysql.OperationalError(
            1045,
            "Access denied for secret_user",
        )

        response = self.client.get("/api/daily-briefs/latest")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret_user", response.get_data(as_text=True))

    @patch("api.load_news_company_links")
    def test_company_news_links_returns_all_links(self, mock_load_links):
        mock_load_links.return_value = [{
            "news_id": 3,
            "company_id": 8,
            "name": "台灣積體電路製造股份有限公司",
            "ticker": "2330",
            "confidence": 0.9,
        }]

        response = self.client.get("/api/company-news-links")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["links"][0]["ticker"], "2330")
        mock_load_links.assert_called_once_with(company_id=None)

    @patch("api.load_news_company_links")
    def test_company_news_links_filters_company(self, mock_load_links):
        mock_load_links.return_value = []

        response = self.client.get("/api/company-news-links?company_id=8")

        self.assertEqual(response.status_code, 200)
        mock_load_links.assert_called_once_with(company_id=8)

    @patch("api.load_news_company_links")
    def test_company_news_links_rejects_invalid_company_id(self, mock_load_links):
        response = self.client.get("/api/company-news-links?company_id=abc")

        self.assertEqual(response.status_code, 400)
        self.assertIn("company_id", response.get_json()["error"])
        mock_load_links.assert_not_called()

    @patch("api.load_market_companies")
    def test_market_companies_returns_available_companies(self, mock_load):
        mock_load.return_value = [{
            "company_id": 8,
            "name": "台灣積體電路製造股份有限公司",
            "ticker": "2330",
            "has_market_prices": True,
            "has_financial_metrics": True,
        }]

        response = self.client.get("/api/market-companies")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["companies"][0]["ticker"], "2330")

    @patch("api.load_company_market_prices")
    def test_company_market_prices_uses_fixed_limit(self, mock_load):
        mock_load.return_value = [{
            "trade_date": "2026-08-11",
            "close_price": 885.0,
        }]

        response = self.client.get("/api/companies/8/market-prices")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["prices"][0]["close_price"], 885.0)
        mock_load.assert_called_once_with(8, limit=90)

    @patch("api.load_company_financial_metrics")
    def test_company_financial_metrics_uses_fixed_limit(self, mock_load):
        mock_load.return_value = [{
            "fiscal_year": 2026,
            "fiscal_quarter": 2,
            "earnings_per_share": 20.15,
        }]

        response = self.client.get("/api/companies/8/financial-metrics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["metrics"][0]["fiscal_quarter"], 2)
        mock_load.assert_called_once_with(8, limit=8)

    @patch("api.load_event_market_observations")
    def test_event_market_observations_marks_non_causal_analysis(self, mock_load):
        mock_load.return_value = [{
            "title": "台積電測試新聞",
            "ticker": "2330",
            "change_percent": 1.25,
            "analysis_type": "observational",
        }]

        response = self.client.get("/api/event-market-observations")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["analysis_type"], "observational")
        self.assertIn("不代表", payload["limitations"][0])
        self.assertEqual(len(payload["observations"]), 1)
        mock_load.assert_called_once_with(limit=20)

    @patch("api.load_watchlist")
    def test_watchlist_returns_tracked_companies(self, mock_load):
        mock_load.return_value = [{
            "company_id": 8,
            "name": "台灣積體電路製造股份有限公司",
            "short_name": "台積電",
            "ticker": "2330",
        }]

        response = self.client.get("/api/watchlist")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["items"][0]["ticker"], "2330")

    @patch("api.add_watchlist_company")
    def test_add_watchlist_returns_created_for_new_item(self, mock_add):
        mock_add.return_value = True

        response = self.client.post("/api/watchlist/8")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"company_id": 8, "added": True})
        mock_add.assert_called_once_with(8)

    @patch("api.remove_watchlist_company")
    def test_remove_watchlist_is_idempotent(self, mock_remove):
        mock_remove.return_value = False

        response = self.client.delete("/api/watchlist/8")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["removed"], False)
        mock_remove.assert_called_once_with(8)

    @patch("api.add_watchlist_company")
    def test_add_watchlist_returns_safe_validation_error(self, mock_add):
        mock_add.side_effect = ValueError("找不到指定公司。")

        response = self.client.post("/api/watchlist/999")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "找不到指定公司。")

    @patch("api.load_personalized_brief")
    def test_personalized_brief_returns_latest_window(self, mock_load):
        mock_load.return_value = {
            "brief_date": "2026-08-12",
            "watchlist_count": 1,
            "article_count": 2,
            "summary": "目前追蹤 1 家公司，本期找到 2 篇相關新聞。",
        }

        response = self.client.get("/api/personalized-brief")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["brief"]["watchlist_count"], 1)
        mock_load.assert_called_once_with()

    @patch("api.load_all_news")
    def test_news_hides_database_error_details(self, mock_load_news):
        mock_load_news.side_effect = pymysql.OperationalError(
            1045,
            "Access denied for secret_user",
        )

        response = self.client.get("/api/news")
        payload = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            payload,
            {"error": "無法讀取 Morning Alpha 新聞資料。"},
        )
        self.assertNotIn("secret_user", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
