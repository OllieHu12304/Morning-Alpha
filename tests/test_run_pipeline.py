"""測試 Morning Alpha 統一資料更新流程。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import run_pipeline  # noqa: E402


class RunPipelineTests(unittest.TestCase):
    def create_step(self, events, name, result):
        """建立會記錄執行順序的假 pipeline step。"""
        def step():
            events.append(name)
            return result

        return step

    def test_run_pipeline_executes_steps_in_order_and_returns_counts(self):
        events = []

        collect_result = (
            2,
            ["TechNews"],
            ["中央社財經 RSS"],
        )
        collect_step = self.create_step(events, "collect", collect_result)
        company_step = self.create_step(events, "companies", 1000)
        link_step = self.create_step(
            events,
            "links",
            {"news_count": 15, "link_count": 6},
        )
        market_step = self.create_step(
            events,
            "market",
            {"source_count": 10, "saved_count": 9, "skipped_count": 1},
        )
        financial_step = self.create_step(
            events,
            "financial",
            {"source_count": 8, "saved_count": 7, "skipped_count": 1},
        )
        brief_step = self.create_step(
            events,
            "brief",
            {"brief_date": "2026-08-12", "article_count": 5},
        )
        export_step = self.create_step(events, "export", 15)
        chart_step = self.create_step(events, "chart", 3)
        keyword_step = self.create_step(events, "keyword", 12)

        with patch.object(
            run_pipeline,
            "collect_and_store_news",
            collect_step,
        ), patch.object(
            run_pipeline,
            "sync_company_data",
            company_step,
        ), patch.object(
            run_pipeline,
            "run_news_company_sync",
            link_step,
        ), patch.object(
            run_pipeline,
            "sync_market_prices",
            market_step,
        ), patch.object(
            run_pipeline,
            "sync_financial_metrics",
            financial_step,
        ), patch.object(
            run_pipeline,
            "generate_and_store_daily_brief",
            brief_step,
        ), patch.object(
            run_pipeline,
            "export_dashboard_news",
            export_step,
        ), patch.object(
            run_pipeline,
            "build_chart_data",
            chart_step,
        ), patch.object(
            run_pipeline,
            "build_keyword_data",
            keyword_step,
        ), patch.object(
            run_pipeline,
            "save_pipeline_run",
        ) as save_history, patch.object(
            run_pipeline,
            "cleanup_history",
            return_value={
                "source_health_events": 0,
                "pipeline_runs": 0,
            },
        ) as cleanup_history:
            summary = run_pipeline.run_pipeline()

        self.assertEqual(events, [
            "collect",
            "companies",
            "links",
            "market",
            "financial",
            "brief",
            "export",
            "chart",
            "keyword",
        ])
        self.assertEqual(summary, {
            "inserted_news": 2,
            "exported_news": 15,
            "chart_groups": 3,
            "exported_keywords": 12,
            "successful_sources": ["TechNews"],
            "failed_sources": ["中央社財經 RSS"],
            "imported_companies": 1000,
            "company_links": 6,
            "market_prices": 9,
            "financial_metrics": 7,
            "daily_brief_date": "2026-08-12",
            "daily_brief_articles": 5,
        })
        saved_run = save_history.call_args.args[0]
        self.assertEqual(saved_run["status"], "success")
        self.assertTrue(all(
            step["status"] == "success"
            for step in saved_run["step_results"]
        ))
        cleanup_history.assert_called_once_with()

    def test_run_pipeline_stops_when_a_step_fails(self):
        collect_result = (2, ["TechNews"], [])

        with patch.object(
            run_pipeline,
            "collect_and_store_news",
            return_value=collect_result,
        ), patch.object(
            run_pipeline,
            "sync_company_data",
            side_effect=ValueError("測試錯誤"),
        ), patch.object(
            run_pipeline,
            "run_news_company_sync",
        ) as link_step, patch.object(
            run_pipeline,
            "sync_market_prices",
        ) as market_step, patch.object(
            run_pipeline,
            "sync_financial_metrics",
        ) as financial_step, patch.object(
            run_pipeline,
            "generate_and_store_daily_brief",
        ) as brief_step, patch.object(
            run_pipeline,
            "export_dashboard_news",
        ) as export_step, patch.object(
            run_pipeline,
            "build_chart_data",
        ) as chart_step, patch.object(
            run_pipeline,
            "build_keyword_data",
        ) as keyword_step, patch.object(
            run_pipeline,
            "save_pipeline_run",
        ) as save_history, patch.object(
            run_pipeline,
            "cleanup_history",
            return_value={
                "source_health_events": 0,
                "pipeline_runs": 0,
            },
        ) as cleanup_history:
            with self.assertRaisesRegex(ValueError, "測試錯誤"):
                run_pipeline.run_pipeline()

        link_step.assert_not_called()
        market_step.assert_not_called()
        financial_step.assert_not_called()
        brief_step.assert_not_called()
        export_step.assert_not_called()
        chart_step.assert_not_called()
        keyword_step.assert_not_called()
        saved_run = save_history.call_args.args[0]
        self.assertEqual(saved_run["status"], "failure")
        self.assertEqual(saved_run["failed_step"], "sync_companies")
        self.assertEqual(saved_run["step_results"][1]["status"], "failure")
        self.assertEqual(saved_run["step_results"][2]["status"], "pending")
        cleanup_history.assert_called_once_with()

    def test_generate_daily_brief_reads_builds_and_saves(self):
        fake_dataframe = object()
        records = [{"title": "測試新聞"}]
        brief = {
            "brief_date": "2026-08-12",
            "article_count": 1,
        }

        with patch.object(
            run_pipeline,
            "load_all_news",
            return_value=fake_dataframe,
        ), patch.object(
            run_pipeline,
            "prepare_dashboard_records",
            return_value=records,
        ) as prepare_records, patch.object(
            run_pipeline,
            "get_latest_brief_date",
            return_value="brief-date",
        ), patch.object(
            run_pipeline,
            "build_daily_brief",
            return_value=brief,
        ) as build_brief, patch.object(
            run_pipeline,
            "save_daily_brief",
        ) as save_brief:
            result = run_pipeline.generate_and_store_daily_brief()

        prepare_records.assert_called_once_with(fake_dataframe)
        build_brief.assert_called_once_with(records, "brief-date")
        save_brief.assert_called_once_with(brief)
        self.assertEqual(result["article_count"], 1)

    def test_sync_company_data_prepares_watchlist_table(self):
        with patch.object(
            run_pipeline,
            "sync_company_directory",
            return_value=1000,
        ), patch.object(
            run_pipeline,
            "ensure_watchlist_table",
        ) as ensure_watchlist:
            result = run_pipeline.sync_company_data()

        self.assertEqual(result, 1000)
        ensure_watchlist.assert_called_once_with()

    def test_main_returns_failure_status_when_pipeline_fails(self):
        with patch.object(
            run_pipeline,
            "run_pipeline",
            side_effect=ValueError("缺少設定"),
        ), patch.object(
            run_pipeline,
            "send_failure_notification",
            return_value=True,
        ) as send_notification:
            result = run_pipeline.main()

        self.assertEqual(result, 1)
        send_notification.assert_called_once_with("缺少設定")

    def test_print_summary_reports_successful_and_failed_sources(self):
        summary = {
            "inserted_news": 5,
            "exported_news": 10,
            "chart_groups": 3,
            "exported_keywords": 20,
            "successful_sources": ["中央社財經 RSS"],
            "failed_sources": ["TechNews"],
            "imported_companies": 1000,
            "company_links": 6,
            "market_prices": 9,
            "financial_metrics": 7,
            "daily_brief_date": "2026-08-12",
            "daily_brief_articles": 5,
        }

        with patch("builtins.print") as print_message:
            run_pipeline.print_summary(summary)

        print_message.assert_any_call("成功來源：中央社財經 RSS")
        print_message.assert_any_call("失敗來源：TechNews")

    def test_collect_saves_failures_before_all_sources_error(self):
        source_results = [
            {
                "source": "technews",
                "source_name": "TechNews",
                "status": "failure",
                "article_count": 0,
                "error_message": "503",
            },
            {
                "source": "cna",
                "source_name": "中央社財經 RSS",
                "status": "failure",
                "article_count": 0,
                "error_message": "timeout",
            },
        ]

        with patch.object(
            run_pipeline,
            "fetch_all_articles_with_status",
            return_value=([], source_results),
        ), patch.object(
            run_pipeline,
            "save_source_health_events",
        ) as save_health, patch.object(
            run_pipeline,
            "save_news",
        ) as save_news:
            with self.assertRaisesRegex(ValueError, "所有新聞來源都失敗"):
                run_pipeline.collect_and_store_news()

        save_health.assert_called_once_with(source_results)
        save_news.assert_not_called()

    def test_history_failure_does_not_replace_original_pipeline_error(self):
        run_result = {
            "status": "failure",
            "error_message": "原始 Pipeline 錯誤",
        }

        with patch.object(
            run_pipeline,
            "save_pipeline_run",
            side_effect=run_pipeline.pymysql.OperationalError(
                2003,
                "MySQL unavailable",
            ),
        ):
            with self.assertLogs("run_pipeline", level="ERROR"):
                result = run_pipeline.save_failed_run_without_hiding_error(
                    run_result
                )

        self.assertIsNone(result)

    def test_history_mysql_error_does_not_expose_connection_details(self):
        error = run_pipeline.pymysql.OperationalError(
            1045,
            "Access denied for secret_user",
        )

        message = run_pipeline.get_history_error_message(error)

        self.assertEqual(
            message,
            "MySQL 操作失敗，請查看 Pipeline log。",
        )
        self.assertNotIn("secret_user", message)

    def test_notification_failure_does_not_change_pipeline_exit_code(self):
        with patch.object(
            run_pipeline,
            "run_pipeline",
            side_effect=ValueError("測試失敗"),
        ), patch.object(
            run_pipeline,
            "send_failure_notification",
            side_effect=run_pipeline.requests.Timeout(
                "https://discord.com/api/webhooks/123/secret-token"
            ),
        ):
            with self.assertLogs("run_pipeline", level="ERROR") as log_output:
                result = run_pipeline.main()

        self.assertEqual(result, 1)
        self.assertNotIn("secret-token", " ".join(log_output.output))

    def test_cleanup_failure_does_not_raise(self):
        with patch.object(
            run_pipeline,
            "cleanup_history",
            side_effect=run_pipeline.pymysql.OperationalError(
                1142,
                "DELETE command denied",
            ),
        ):
            with self.assertLogs("run_pipeline", level="ERROR"):
                result = run_pipeline.cleanup_history_without_hiding_result()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
