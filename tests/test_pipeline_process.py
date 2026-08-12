"""測試 Dashboard 使用的 Pipeline subprocess 管理。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import pipeline_process  # noqa: E402


class PipelineProcessTests(unittest.TestCase):
    def setUp(self):
        pipeline_process._pipeline_process = None
        pipeline_process._pipeline_started_at = None
        pipeline_process._pipeline_finished_at = None

    def tearDown(self):
        pipeline_process._pipeline_process = None
        pipeline_process._pipeline_started_at = None
        pipeline_process._pipeline_finished_at = None

    @patch("pipeline_process.utc_now_iso", return_value="2026-08-12T04:00:00+00:00")
    @patch("pipeline_process.subprocess.Popen")
    def test_start_uses_current_python_and_project_directory(
        self,
        mock_popen,
        mock_now,
    ):
        process = MagicMock()
        process.poll.return_value = None
        mock_popen.return_value = process

        started, status = pipeline_process.start_pipeline()

        self.assertTrue(started)
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["started_at"], "2026-08-12T04:00:00+00:00")
        mock_popen.assert_called_once_with(
            [
                sys.executable,
                str(pipeline_process.PIPELINE_SCRIPT),
            ],
            cwd=pipeline_process.PROJECT_DIRECTORY,
        )
        mock_now.assert_called_once_with()

    @patch("pipeline_process.subprocess.Popen")
    def test_start_rejects_duplicate_running_process(self, mock_popen):
        process = MagicMock()
        process.poll.return_value = None
        pipeline_process._pipeline_process = process
        pipeline_process._pipeline_started_at = "2026-08-12T04:00:00+00:00"

        started, status = pipeline_process.start_pipeline()

        self.assertFalse(started)
        self.assertEqual(status["status"], "running")
        mock_popen.assert_not_called()

    @patch("pipeline_process.utc_now_iso", return_value="2026-08-12T04:01:00+00:00")
    def test_status_reports_successful_completion(self, mock_now):
        process = MagicMock()
        process.poll.return_value = 0
        pipeline_process._pipeline_process = process
        pipeline_process._pipeline_started_at = "2026-08-12T04:00:00+00:00"

        status = pipeline_process.get_pipeline_status()

        self.assertEqual(status["status"], "success")
        self.assertEqual(status["exit_code"], 0)
        self.assertEqual(status["finished_at"], "2026-08-12T04:01:00+00:00")
        mock_now.assert_called_once_with()

    def test_status_reports_failed_completion(self):
        process = MagicMock()
        process.poll.return_value = 1
        pipeline_process._pipeline_process = process
        pipeline_process._pipeline_started_at = "2026-08-12T04:00:00+00:00"
        pipeline_process._pipeline_finished_at = "2026-08-12T04:01:00+00:00"

        status = pipeline_process.get_pipeline_status()

        self.assertEqual(status["status"], "failure")
        self.assertEqual(status["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
