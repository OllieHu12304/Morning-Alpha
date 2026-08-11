"""測試每日晨報 MySQL 儲存格式。"""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from daily_brief_store import (  # noqa: E402
    decode_brief_payload,
    fetch_daily_briefs,
    prepare_daily_brief_record,
    upsert_daily_brief,
)


def make_brief(article_count=2):
    """建立儲存 tests 使用的晨報。"""
    return {
        "brief_date": "2026-08-12",
        "window_start": "2026-08-11T07:00:00+08:00",
        "window_end": "2026-08-12T07:00:00+08:00",
        "article_count": article_count,
        "summary": "測試晨報",
        "sources": [],
        "categories": [],
        "keywords": [],
        "highlights": [],
        "limitations": [],
    }


class DailyBriefStoreTests(unittest.TestCase):
    def test_prepare_record_converts_time_and_json(self):
        record = prepare_daily_brief_record(make_brief())

        self.assertEqual(record[0], date(2026, 8, 12))
        self.assertEqual(record[1], datetime(2026, 8, 11, 7, 0))
        self.assertEqual(record[2], datetime(2026, 8, 12, 7, 0))
        self.assertEqual(record[3], 2)
        self.assertIn('"summary": "測試晨報"', record[4])

    def test_upsert_uses_parameterized_record(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        changed_count = upsert_daily_brief(connection, make_brief())

        self.assertEqual(changed_count, 1)
        self.assertEqual(cursor.execute.call_count, 1)
        parameters = cursor.execute.call_args.args[1]
        self.assertEqual(parameters[0], date(2026, 8, 12))

    def test_fetch_briefs_decodes_mysql_json(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(b'{"brief_date":"2026-08-12"}',)]

        briefs = fetch_daily_briefs(connection, limit=10)

        self.assertEqual(briefs, [{"brief_date": "2026-08-12"}])
        cursor.execute.assert_called_once()

    def test_decode_rejects_non_object_payload(self):
        with self.assertRaisesRegex(ValueError, "object"):
            decode_brief_payload("[]")

    def test_rejects_invalid_time_window(self):
        brief = make_brief()
        brief["window_start"] = brief["window_end"]

        with self.assertRaisesRegex(ValueError, "開始"):
            prepare_daily_brief_record(brief)


if __name__ == "__main__":
    unittest.main()
