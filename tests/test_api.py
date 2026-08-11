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

    @patch("api.load_all_news")
    def test_news_returns_grouped_dashboard_records(self, mock_load_news):
        mock_load_news.return_value = create_test_dataframe()

        response = self.client.get("/api/news")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["news"][0]["source"], "technews")
        self.assertIn("event_group_id", payload["news"][0])
        self.assertNotIn("id", payload["news"][0])

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
            "2026-08-11T09:00:00",
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
