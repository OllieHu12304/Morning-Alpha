"""測試 Morning Alpha 初學者友善啟動器。"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIRECTORY))

import start  # noqa: E402


class StartTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = patch("builtins.print")
        self.print_patcher.start()
        self.addCleanup(self.print_patcher.stop)

    def test_finds_mac_or_linux_virtual_environment(self):
        with TemporaryDirectory() as temporary_directory:
            project_directory = Path(temporary_directory)
            unix_python = project_directory / ".venv" / "bin" / "python"
            unix_python.parent.mkdir(parents=True)
            unix_python.touch()

            result = start.find_venv_python(project_directory)

        self.assertEqual(result, unix_python)

    @patch("start.open_dashboard")
    @patch("start.is_morning_alpha_running", return_value=True)
    def test_existing_api_opens_without_starting_another_process(
        self,
        mock_running,
        mock_open_dashboard,
    ):
        with patch("start.subprocess.Popen") as mock_popen:
            result = start.run()

        self.assertEqual(result, 0)
        mock_open_dashboard.assert_called_once_with()
        mock_popen.assert_not_called()

    @patch("start.is_api_port_in_use", return_value=True)
    @patch("start.is_morning_alpha_running", return_value=False)
    def test_rejects_port_used_by_another_program(
        self,
        mock_running,
        mock_port_in_use,
    ):
        with patch("start.subprocess.Popen") as mock_popen:
            result = start.run()

        self.assertEqual(result, 1)
        mock_popen.assert_not_called()

    @patch("start.find_venv_python", return_value=None)
    @patch("start.is_api_port_in_use", return_value=False)
    @patch("start.is_morning_alpha_running", return_value=False)
    def test_reports_missing_virtual_environment(
        self,
        mock_running,
        mock_port_in_use,
        mock_find_python,
    ):
        result = start.run()

        self.assertEqual(result, 1)

    @patch("start.has_database_config", return_value=True)
    @patch("start.find_venv_python")
    @patch("start.is_api_port_in_use", return_value=False)
    @patch("start.is_morning_alpha_running", return_value=False)
    @patch("start.open_dashboard")
    @patch("start.wait_for_api", return_value=True)
    @patch("start.subprocess.Popen")
    def test_starts_api_with_project_virtual_environment(
        self,
        mock_popen,
        mock_wait_for_api,
        mock_open_dashboard,
        mock_running,
        mock_port_in_use,
        mock_find_python,
        mock_has_config,
    ):
        venv_python = Path("/project/.venv/bin/python")
        process = MagicMock()
        process.wait.return_value = 0
        mock_find_python.return_value = venv_python
        mock_popen.return_value = process

        result = start.run()

        self.assertEqual(result, 0)
        mock_popen.assert_called_once_with(
            [str(venv_python), str(start.API_SCRIPT)],
            cwd=start.PROJECT_DIRECTORY,
        )
        mock_wait_for_api.assert_called_once_with(process)
        mock_open_dashboard.assert_called_once_with()

    @patch("start.has_database_config", return_value=True)
    @patch("start.find_venv_python", return_value=Path("/venv/python"))
    @patch("start.is_api_port_in_use", return_value=False)
    @patch("start.is_morning_alpha_running", return_value=False)
    @patch("start.subprocess.Popen", side_effect=OSError("permission denied"))
    def test_reports_api_process_start_failure(
        self,
        mock_popen,
        mock_running,
        mock_port_in_use,
        mock_find_python,
        mock_has_config,
    ):
        result = start.run()

        self.assertEqual(result, 1)

    @patch("start.has_database_config", return_value=True)
    @patch("start.find_venv_python", return_value=Path("/venv/python"))
    @patch("start.is_api_port_in_use", return_value=False)
    @patch("start.is_morning_alpha_running", return_value=False)
    @patch("start.wait_for_api", return_value=True)
    @patch("start.subprocess.Popen")
    def test_control_c_stops_started_api(
        self,
        mock_popen,
        mock_wait_for_api,
        mock_running,
        mock_port_in_use,
        mock_find_python,
        mock_has_config,
    ):
        process = MagicMock()
        process.wait.side_effect = KeyboardInterrupt
        mock_popen.return_value = process

        with patch("start.open_dashboard"), patch(
            "start.stop_api_process"
        ) as mock_stop:
            result = start.run()

        self.assertEqual(result, 0)
        mock_stop.assert_called_once_with(process)


if __name__ == "__main__":
    unittest.main()
