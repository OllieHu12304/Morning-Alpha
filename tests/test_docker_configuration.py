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


if __name__ == "__main__":
    unittest.main()
