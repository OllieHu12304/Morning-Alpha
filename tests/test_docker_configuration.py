"""測試 Docker build 不會包含本機 Python 環境。"""

from pathlib import Path
import unittest


PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]


class DockerConfigurationTests(unittest.TestCase):
    def test_dockerignore_excludes_local_python_environments(self):
        dockerignore = (
            PROJECT_DIRECTORY / ".dockerignore"
        ).read_text(encoding="utf-8").splitlines()

        self.assertIn(".venv", dockerignore)
        self.assertIn(".conda", dockerignore)

    def test_dashboard_api_port_is_bound_to_localhost(self):
        compose = (PROJECT_DIRECTORY / "compose.yaml").read_text(
            encoding="utf-8",
        )

        self.assertIn(
            '"127.0.0.1:${API_PORT:-5050}:5050"',
            compose,
        )


if __name__ == "__main__":
    unittest.main()
