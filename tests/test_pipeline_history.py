"""測試完整 Pipeline 執行歷史的保存與讀取。"""

import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import pipeline_history  # noqa: E402


class PipelineHistoryTests(unittest.TestCase):
    def create_success_result(self):
        step_results = pipeline_history.create_pending_step_results()

        for step, _ in pipeline_history.PIPELINE_STEPS:
            pipeline_history.update_step_result(
                step_results,
                step,
                "success",
                25,
                {"count": 1},
            )

        return {
            "status": "success",
            "started_at": datetime(2026, 8, 11, 10, 0, 0),
            "finished_at": datetime(2026, 8, 11, 10, 0, 1),
            "duration_ms": 1000,
            "failed_step": "不應保存",
            "step_results": step_results,
            "error_message": "不應保存",
        }

    def test_create_pending_results_uses_fixed_four_steps(self):
        results = pipeline_history.create_pending_step_results()

        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["step"], "collect_news")
        self.assertTrue(all(result["status"] == "pending" for result in results))

    def test_update_step_result_changes_only_requested_step(self):
        results = pipeline_history.create_pending_step_results()

        pipeline_history.update_step_result(
            results,
            "export_news",
            "failure",
            42,
        )

        self.assertEqual(results[0]["status"], "pending")
        self.assertEqual(results[1]["status"], "failure")
        self.assertEqual(results[1]["duration_ms"], 42)

    def test_prepare_success_removes_failure_fields(self):
        record = pipeline_history.prepare_pipeline_run_record(
            self.create_success_result()
        )

        self.assertEqual(record[0], "success")
        self.assertIsNone(record[4])
        self.assertIsNone(record[6])
        self.assertEqual(len(json.loads(record[5])), 4)

    def test_prepare_failure_cleans_error_message(self):
        result = self.create_success_result()
        result["status"] = "failure"
        result["failed_step"] = "export_news"
        result["error_message"] = "JSON\n  格式錯誤"
        result["step_results"] = pipeline_history.create_pending_step_results()
        pipeline_history.update_step_result(
            result["step_results"],
            "collect_news",
            "success",
            25,
            {"inserted_news": 1},
        )
        pipeline_history.update_step_result(
            result["step_results"],
            "export_news",
            "failure",
            25,
        )

        record = pipeline_history.prepare_pipeline_run_record(result)

        self.assertEqual(record[4], "export_news")
        self.assertEqual(record[6], "JSON 格式錯誤")

    def test_insert_pipeline_run_uses_parameters(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.lastrowid = 8

        run_id = pipeline_history.insert_pipeline_run(
            connection,
            self.create_success_result(),
        )

        self.assertEqual(run_id, 8)
        cursor.execute.assert_called_once()
        parameters = cursor.execute.call_args.args[1]
        self.assertEqual(parameters[0], "success")

    def test_build_records_parses_mysql_json(self):
        result = self.create_success_result()
        parameters = pipeline_history.prepare_pipeline_run_record(result)
        columns = [
            "id",
            "status",
            "started_at",
            "finished_at",
            "duration_ms",
            "failed_step",
            "step_results",
            "error_message",
        ]
        rows = [(7, *parameters)]

        records = pipeline_history.build_pipeline_run_records(rows, columns)

        self.assertEqual(records[0]["id"], 7)
        self.assertEqual(records[0]["status"], "success")
        self.assertEqual(len(records[0]["step_results"]), 4)
        self.assertEqual(records[0]["started_at"], "2026-08-11T10:00:00+00:00")

    def test_migration_defines_pipeline_runs_json(self):
        migration_sql = (
            PROJECT_DIRECTORY
            / "sql"
            / "006_create_pipeline_runs.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS pipeline_runs", migration_sql)
        self.assertIn("step_results JSON NOT NULL", migration_sql)
        self.assertNotIn("UPDATE pipeline_runs", migration_sql)


if __name__ == "__main__":
    unittest.main()
