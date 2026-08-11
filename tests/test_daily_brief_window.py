"""測試每日晨報的台北時間範圍。"""

import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from daily_brief_window import (  # noqa: E402
    get_brief_window,
    get_latest_brief_date,
    to_database_datetime,
)


TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")


class DailyBriefWindowTests(unittest.TestCase):
    def test_window_uses_previous_morning_to_current_morning(self):
        start_time, end_time = get_brief_window(date(2026, 8, 12))

        self.assertEqual(
            start_time,
            datetime(2026, 8, 11, 7, tzinfo=TAIPEI_TIMEZONE),
        )
        self.assertEqual(
            end_time,
            datetime(2026, 8, 12, 7, tzinfo=TAIPEI_TIMEZONE),
        )

    def test_latest_date_uses_previous_day_before_seven(self):
        current_time = datetime(
            2026,
            8,
            12,
            6,
            59,
            tzinfo=TAIPEI_TIMEZONE,
        )

        self.assertEqual(
            get_latest_brief_date(current_time),
            date(2026, 8, 11),
        )

    def test_latest_date_uses_current_day_at_seven(self):
        current_time = datetime(
            2026,
            8,
            12,
            7,
            0,
            tzinfo=TAIPEI_TIMEZONE,
        )

        self.assertEqual(
            get_latest_brief_date(current_time),
            date(2026, 8, 12),
        )

    def test_latest_date_converts_utc_to_taipei(self):
        current_time = datetime(2026, 8, 11, 23, 0, tzinfo=timezone.utc)

        self.assertEqual(
            get_latest_brief_date(current_time),
            date(2026, 8, 12),
        )

    def test_database_datetime_removes_timezone_after_conversion(self):
        utc_time = datetime(2026, 8, 11, 23, 0, tzinfo=timezone.utc)

        self.assertEqual(
            to_database_datetime(utc_time),
            datetime(2026, 8, 12, 7, 0),
        )

    def test_rejects_naive_current_time(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            get_latest_brief_date(datetime(2026, 8, 12, 7, 0))


if __name__ == "__main__":
    unittest.main()
