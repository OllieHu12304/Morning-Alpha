"""測試來源與 Pipeline history 的保留期限清理。"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import history_retention  # noqa: E402


class HistoryRetentionTests(unittest.TestCase):
    @patch("history_retention.load_environment")
    def test_retention_days_defaults_to_ninety(self, mock_load_environment):
        with patch.dict(os.environ, {}, clear=True):
            result = history_retention.get_retention_days()

        self.assertEqual(result, 90)
        mock_load_environment.assert_called_once_with()

    @patch("history_retention.load_environment")
    def test_retention_days_rejects_out_of_range_value(
        self,
        mock_load_environment,
    ):
        with patch.dict(
            os.environ,
            {"HISTORY_RETENTION_DAYS": "0"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "1 到 3650"):
                history_retention.get_retention_days()

        mock_load_environment.assert_called_once_with()

    def test_delete_old_history_only_targets_history_tables(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 2
        cutoff = datetime(2026, 5, 13, 0, 0, 0)

        result = history_retention.delete_old_history(connection, cutoff)

        self.assertEqual(result, {
            "source_health_events": 2,
            "pipeline_runs": 2,
        })
        executed_sql = " ".join(
            call.args[0]
            for call in cursor.execute.call_args_list
        )
        self.assertIn("DELETE FROM source_health_events", executed_sql)
        self.assertIn("DELETE FROM pipeline_runs", executed_sql)
        self.assertNotIn("news_records", executed_sql)
        self.assertEqual(cursor.execute.call_count, 3)
        self.assertEqual(
            cursor.execute.call_args_list[0].args[0],
            "SET time_zone = '+00:00';",
        )

    def test_example_environment_includes_retention_settings(self):
        environment_example = (
            PROJECT_DIRECTORY / ".env.example"
        ).read_text(encoding="utf-8")

        self.assertIn("HISTORY_RETENTION_DAYS=90", environment_example)
        self.assertIn("PIPELINE_FAILURE_WEBHOOK_URL=", environment_example)


if __name__ == "__main__":
    unittest.main()
