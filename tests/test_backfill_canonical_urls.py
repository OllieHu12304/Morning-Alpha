"""測試既有 canonical URLs 的稽核與受控 backfill。"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from backfill_canonical_urls import (  # noqa: E402
    apply_backfill,
    build_backfill_plan,
    export_audit_report,
)
import backfill_canonical_urls  # noqa: E402


class BackfillCanonicalUrlsTests(unittest.TestCase):
    def test_build_plan_normalizes_urls_and_creates_hashes(self):
        records = [{
            "id": 1,
            "title": "測試新聞",
            "url": "https://www.example.com/news?utm_source=test",
            "canonical_url": "https://www.example.com/news?utm_source=test",
        }]

        report, updates = build_backfill_plan(records)

        self.assertEqual(report["total_records"], 1)
        self.assertEqual(report["changed_urls"], 1)
        self.assertEqual(report["conflict_groups"], [])
        self.assertEqual(updates[0]["canonical_url"], "https://example.com/news")
        self.assertEqual(len(updates[0]["canonical_url_hash"]), 64)

    def test_build_plan_reports_canonical_url_conflicts(self):
        records = [
            {
                "id": 1,
                "title": "第一篇",
                "url": "https://example.com/news?utm_source=one",
                "canonical_url": "https://example.com/news?utm_source=one",
            },
            {
                "id": 2,
                "title": "第二篇",
                "url": "https://www.example.com/news#content",
                "canonical_url": "https://www.example.com/news#content",
            },
        ]

        report, _ = build_backfill_plan(records)

        self.assertEqual(len(report["conflict_groups"]), 1)
        self.assertEqual(
            report["conflict_groups"][0]["canonical_url"],
            "https://example.com/news",
        )
        self.assertEqual(
            len(report["conflict_groups"][0]["records"]),
            2,
        )

    def test_build_plan_reports_invalid_urls(self):
        records = [{
            "id": 1,
            "title": "錯誤網址",
            "url": "not-a-url",
            "canonical_url": "not-a-url",
        }]

        report, updates = build_backfill_plan(records)

        self.assertEqual(len(report["invalid_records"]), 1)
        self.assertEqual(updates, [])

    def test_export_audit_report_writes_utf8_json(self):
        report = {
            "total_records": 1,
            "valid_records": 1,
            "changed_urls": 0,
            "invalid_records": [],
            "conflict_groups": [],
        }

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "audit.json"
            export_audit_report(report, output_path)

            with output_path.open(encoding="utf-8") as json_file:
                self.assertEqual(json.load(json_file), report)

    def test_apply_backfill_uses_parameterized_update(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.executemany.return_value = 2
        updates = [
            {
                "id": 1,
                "canonical_url": "https://example.com/one",
                "canonical_url_hash": "a" * 64,
            },
            {
                "id": 2,
                "canonical_url": "https://example.com/two",
                "canonical_url_hash": "b" * 64,
            },
        ]

        updated_count = apply_backfill(connection, updates)

        self.assertEqual(updated_count, 2)
        parameters = cursor.executemany.call_args.args[1]
        self.assertEqual(parameters[0][2], 1)
        self.assertEqual(parameters[1][2], 2)

    def test_run_backfill_does_not_write_when_conflicts_exist(self):
        connection = Mock()
        records = [
            {
                "id": 1,
                "title": "第一篇",
                "url": "https://example.com/news?utm_source=one",
                "canonical_url": "https://example.com/news?utm_source=one",
            },
            {
                "id": 2,
                "title": "第二篇",
                "url": "https://www.example.com/news#content",
                "canonical_url": "https://www.example.com/news#content",
            },
        ]

        with patch.object(
            backfill_canonical_urls,
            "get_database_config",
            return_value={},
        ), patch.object(
            backfill_canonical_urls,
            "connect_to_database",
            return_value=connection,
        ), patch.object(
            backfill_canonical_urls,
            "fetch_news_records",
            return_value=records,
        ), patch.object(
            backfill_canonical_urls,
            "export_audit_report",
        ), patch.object(
            backfill_canonical_urls,
            "apply_backfill",
        ) as apply_mock:
            with self.assertRaisesRegex(ValueError, "衝突"):
                backfill_canonical_urls.run_backfill(apply_changes=True)

        apply_mock.assert_not_called()
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
