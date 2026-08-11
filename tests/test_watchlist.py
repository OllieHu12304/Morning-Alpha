"""測試本機單一使用者追蹤清單。"""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from watchlist import (  # noqa: E402
    build_watchlist_records,
    delete_watchlist_item,
    insert_watchlist_item,
    validate_company_id,
)


class WatchlistTests(unittest.TestCase):
    def test_validate_company_id_rejects_invalid_values(self):
        for value in [True, "8", 0, -1]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "正整數"):
                    validate_company_id(value)

    def test_insert_watchlist_item_returns_true_for_new_company(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (8,)
        cursor.rowcount = 1

        added = insert_watchlist_item(connection, 8)

        self.assertTrue(added)
        self.assertEqual(cursor.execute.call_count, 2)
        self.assertEqual(cursor.execute.call_args.args[1], (8,))

    def test_insert_watchlist_item_rejects_missing_company(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        with self.assertRaisesRegex(ValueError, "找不到"):
            insert_watchlist_item(connection, 999)

        self.assertEqual(cursor.execute.call_count, 1)

    def test_delete_watchlist_item_reports_existing_row(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        removed = delete_watchlist_item(connection, 8)

        self.assertTrue(removed)
        self.assertEqual(cursor.execute.call_args.args[1], (8,))

    def test_build_watchlist_records_formats_created_at(self):
        rows = [(
            1,
            8,
            "台灣積體電路製造股份有限公司",
            "台積電",
            "半導體業",
            "2330",
            "TWSE",
            datetime(2026, 8, 11, 10, 0),
        )]
        columns = [
            "id",
            "company_id",
            "name",
            "short_name",
            "industry",
            "ticker",
            "exchange",
            "created_at",
        ]

        records = build_watchlist_records(rows, columns)

        self.assertEqual(records[0]["ticker"], "2330")
        self.assertEqual(records[0]["created_at"], "2026-08-11T10:00:00")

    def test_migration_defines_unique_company_watchlist(self):
        migration_sql = (
            PROJECT_DIRECTORY / "sql" / "012_create_watchlist_items.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS watchlist_items", migration_sql)
        self.assertIn("UNIQUE KEY unique_watchlist_company", migration_sql)
        self.assertIn("FOREIGN KEY (company_id)", migration_sql)


if __name__ == "__main__":
    unittest.main()
