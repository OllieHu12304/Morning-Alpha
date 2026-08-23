"""測試本機 Python Pipeline scheduler。"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import scheduler  # noqa: E402


class SchedulerTests(unittest.TestCase):
    def test_get_interval_seconds_defaults_to_twenty_four_hours(self):
        with patch.dict(os.environ, {}, clear=True):
            interval_seconds = scheduler.get_interval_seconds()

        self.assertEqual(interval_seconds, 24 * 60 * 60)

    def test_get_interval_seconds_converts_positive_integer_hours(self):
        with patch.dict(
            os.environ,
            {"PIPELINE_INTERVAL_HOURS": "6"},
            clear=True,
        ):
            interval_seconds = scheduler.get_interval_seconds()

        self.assertEqual(interval_seconds, 6 * 60 * 60)

    def test_get_interval_seconds_rejects_invalid_value(self):
        invalid_values = ["0", "-1", "one-day"]

        for invalid_value in invalid_values:
            with self.subTest(value=invalid_value):
                with patch.dict(
                    os.environ,
                    {"PIPELINE_INTERVAL_HOURS": invalid_value},
                    clear=True,
                ):
                    with self.assertRaisesRegex(ValueError, "正整數"):
                        scheduler.get_interval_seconds()

    def test_run_scheduler_runs_immediately_then_waits(self):
        completed_process = Mock(returncode=0)

        with patch.dict(
            os.environ,
            {"PIPELINE_INTERVAL_HOURS": "2"},
            clear=True,
        ), patch.object(
            scheduler.subprocess,
            "run",
            return_value=completed_process,
        ) as run_process, patch.object(
            scheduler.time,
            "sleep",
        ) as sleep:
            scheduler.run_scheduler(max_runs=2)

        self.assertEqual(run_process.call_count, 2)
        sleep.assert_called_once_with(2 * 60 * 60)

    def test_run_scheduler_continues_after_pipeline_failure(self):
        failed_process = Mock(returncode=1)
        successful_process = Mock(returncode=0)

        with patch.object(
            scheduler.subprocess,
            "run",
            side_effect=[failed_process, successful_process],
        ) as run_process, patch.object(
            scheduler.time,
            "sleep",
        ):
            scheduler.run_scheduler(max_runs=2)

        self.assertEqual(run_process.call_count, 2)


if __name__ == "__main__":
    unittest.main()
