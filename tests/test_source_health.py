"""測試新聞來源健康狀態的保存與摘要。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import source_health  # noqa: E402


class SourceHealthTests(unittest.TestCase):
    def test_prepare_records_cleans_failure_message(self):
        records = source_health.prepare_source_health_records([{
            "source": "technews",
            "status": "failure",
            "article_count": 0,
            "error_message": "503\n  Server Error",
        }])

        self.assertEqual(records, [(
            "technews",
            "failure",
            0,
            "503 Server Error",
        )])

    def test_prepare_records_removes_error_from_success(self):
        records = source_health.prepare_source_health_records([{
            "source": "cna",
            "status": "success",
            "article_count": 20,
            "error_message": "不應保存",
        }])

        self.assertEqual(records, [("cna", "success", 20, None)])

    def test_prepare_records_rejects_invalid_status(self):
        with self.assertRaisesRegex(ValueError, "source 或 status"):
            source_health.prepare_source_health_records([{
                "source": "technews",
                "status": "unknown",
                "article_count": 0,
            }])

    def test_insert_events_uses_parameterized_records(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.executemany.return_value = 2
        source_results = [
            {
                "source": "technews",
                "status": "failure",
                "article_count": 0,
                "error_message": "503",
            },
            {
                "source": "cna",
                "status": "success",
                "article_count": 12,
                "error_message": None,
            },
        ]

        inserted_count = source_health.insert_source_health_events(
            connection,
            source_results,
        )

        self.assertEqual(inserted_count, 2)
        self.assertEqual(cursor.executemany.call_count, 1)

    def test_build_summary_keeps_latest_status_and_last_success(self):
        column_names = [
            "source",
            "status",
            "article_count",
            "error_message",
            "attempted_at",
            "attempted_at_epoch",
        ]
        rows = [
            (
                "technews",
                "failure",
                0,
                "503 Server Error",
                datetime(2026, 8, 11, 12, 0, 0),
                1786449600,
            ),
            (
                "technews",
                "success",
                5,
                None,
                datetime(2026, 8, 10, 12, 0, 0),
                1786363200,
            ),
            (
                "cna",
                "success",
                15,
                None,
                datetime(2026, 8, 11, 12, 1, 0),
                1786449660,
            ),
        ]

        summaries = source_health.build_source_health_summary(
            rows,
            column_names,
        )

        self.assertEqual(summaries, [
            {
                "source": "cna",
                "status": "success",
                "article_count": 15,
                "error_message": None,
                "last_attempt_at": "2026-08-11T12:01:00+00:00",
                "last_success_at": "2026-08-11T12:01:00+00:00",
            },
            {
                "source": "technews",
                "status": "failure",
                "article_count": 0,
                "error_message": "503 Server Error",
                "last_attempt_at": "2026-08-11T12:00:00+00:00",
                "last_success_at": "2026-08-10T12:00:00+00:00",
            },
        ])

    def test_epoch_time_does_not_double_apply_local_timezone(self):
        self.assertEqual(
            source_health.format_timestamp(1786433340),
            "2026-08-11T07:29:00+00:00",
        )

    def test_read_query_uses_timezone_independent_epoch(self):
        self.assertIn(
            "UNIX_TIMESTAMP(attempted_at)",
            source_health.READ_SOURCE_HEALTH_SQL,
        )

    def test_migration_defines_append_only_table(self):
        migration_sql = (
            PROJECT_DIRECTORY
            / "sql"
            / "005_create_source_health_events.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS source_health_events", migration_sql)
        self.assertIn("attempted_at TIMESTAMP", migration_sql)
        self.assertNotIn("UPDATE source_health_events", migration_sql)


if __name__ == "__main__":
    unittest.main()
