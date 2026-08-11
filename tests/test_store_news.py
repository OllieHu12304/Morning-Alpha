"""測試新聞資料寫入 MySQL 前的準備邏輯與 schema。"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import store_news  # noqa: E402


class StoreNewsTests(unittest.TestCase):
    def test_get_database_config_loads_dotenv_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            env_path = Path(temporary_directory) / ".env"
            env_path.write_text(
                "MYSQL_USER=dotenv_user\n"
                "MYSQL_PASSWORD=dotenv_password\n"
                "MYSQL_DATABASE=dotenv_database\n",
                encoding="utf-8",
            )

            with patch.object(store_news, "ENV_PATH", env_path):
                with patch.dict(os.environ, {}, clear=True):
                    config = store_news.get_database_config()

        self.assertEqual(config["user"], "dotenv_user")
        self.assertEqual(config["password"], "dotenv_password")
        self.assertEqual(config["database"], "dotenv_database")
        self.assertEqual(config["host"], "localhost")
        self.assertEqual(config["port"], 3306)

    def test_shell_environment_overrides_dotenv_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            env_path = Path(temporary_directory) / ".env"
            env_path.write_text(
                "MYSQL_USER=dotenv_user\n"
                "MYSQL_PASSWORD=dotenv_password\n",
                encoding="utf-8",
            )
            shell_environment = {
                "MYSQL_USER": "shell_user",
                "MYSQL_PASSWORD": "shell_password",
            }

            with patch.object(store_news, "ENV_PATH", env_path):
                with patch.dict(os.environ, shell_environment, clear=True):
                    config = store_news.get_database_config()

        self.assertEqual(config["user"], "shell_user")
        self.assertEqual(config["password"], "shell_password")

    def test_prepare_news_records_adds_source_and_canonical_url(self):
        dataframe = pd.DataFrame([{
            "source": "technews",
            "source_category": None,
            "title": "測試新聞",
            "publish_time": pd.Timestamp("2026-08-11 09:30:00"),
            "url": (
                "https://www.technews.tw/example/"
                "?utm_source=test#content"
            ),
        }])

        records = store_news.prepare_news_records(dataframe)

        self.assertEqual(records, [(
            "technews",
            None,
            "其他",
            "測試新聞",
            pd.Timestamp("2026-08-11 09:30:00").to_pydatetime(),
            "https://www.technews.tw/example/?utm_source=test#content",
            "https://technews.tw/example/",
            "dcb385a32bd81afddcfe4e5bba2a8027ca22dc4a63a195c6684d0c00cd919f58",
        )])

    def test_prepare_news_records_rejects_missing_title(self):
        dataframe = pd.DataFrame([{
            "source": "technews",
            "source_category": None,
            "title": "",
            "publish_time": pd.Timestamp("2026-08-11 09:30:00"),
            "url": "https://technews.tw/example/",
        }])

        with self.assertRaisesRegex(ValueError, "空白欄位"):
            store_news.prepare_news_records(dataframe)

    def test_prepare_news_records_converts_nan_category_to_none(self):
        dataframe = pd.DataFrame([
            {
                "source": "technews",
                "source_category": None,
                "title": "科技新聞",
                "publish_time": pd.Timestamp("2026-08-11 09:30:00"),
                "url": "https://technews.tw/technology/",
            },
            {
                "source": "cna",
                "source_category": "產經證券",
                "title": "財經新聞",
                "publish_time": pd.Timestamp("2026-08-11 09:00:00"),
                "url": "https://www.cna.com.tw/news/afe/1.aspx",
            },
        ])

        records = store_news.prepare_news_records(dataframe)

        self.assertIsNone(records[0][1])
        self.assertEqual(records[1][1], "產經證券")

    def test_prepare_news_records_rejects_invalid_publish_time(self):
        dataframe = pd.DataFrame([{
            "source": "technews",
            "source_category": None,
            "title": "測試新聞",
            "publish_time": pd.NaT,
            "url": "https://technews.tw/example/",
        }])

        with self.assertRaisesRegex(ValueError, "發布時間"):
            store_news.prepare_news_records(dataframe)

    def test_create_table_sql_contains_news_quality_columns(self):
        sql = store_news.CREATE_TABLE_SQL

        self.assertIn("source VARCHAR(100) NOT NULL", sql)
        self.assertIn("source_category VARCHAR(100) NULL", sql)
        self.assertIn("analysis_category VARCHAR(100) NULL", sql)
        self.assertIn("canonical_url VARCHAR(1000) NOT NULL", sql)
        self.assertIn("canonical_url_hash CHAR(64)", sql)
        self.assertIn("unique_canonical_url_hash", sql)
        self.assertNotIn("unique_news_title", sql)

    def test_insert_sql_writes_source_and_canonical_url(self):
        sql = store_news.INSERT_NEWS_SQL

        self.assertIn("source", sql)
        self.assertIn("source_category", sql)
        self.assertIn("analysis_category", sql)
        self.assertIn("canonical_url", sql)
        self.assertIn("canonical_url_hash", sql)
        self.assertEqual(sql.count("%s"), 8)

    def test_migration_backfills_existing_rows(self):
        migration_path = (
            PROJECT_DIRECTORY
            / "sql"
            / "001_add_news_quality_fields.sql"
        )
        migration_sql = migration_path.read_text(encoding="utf-8")

        self.assertIn("SET source = 'technews'", migration_sql)
        self.assertIn("SET canonical_url = url", migration_sql)
        self.assertNotIn("DROP INDEX unique_news_title", migration_sql)

    def test_hash_migrations_keep_title_unique_for_next_feature(self):
        prepare_path = (
            PROJECT_DIRECTORY
            / "sql"
            / "002_add_canonical_url_hash.sql"
        )
        enforce_path = (
            PROJECT_DIRECTORY
            / "sql"
            / "003_enforce_canonical_url_uniqueness.sql"
        )
        prepare_sql = prepare_path.read_text(encoding="utf-8")
        enforce_sql = enforce_path.read_text(encoding="utf-8")

        self.assertIn("ADD COLUMN canonical_url_hash", prepare_sql)
        self.assertIn("unique_canonical_url_hash", enforce_sql)
        self.assertNotIn("DROP INDEX unique_news_title", enforce_sql)

    def test_title_unique_migration_preserves_canonical_unique(self):
        migration_path = (
            PROJECT_DIRECTORY
            / "sql"
            / "004_remove_title_unique.sql"
        )
        migration_sql = migration_path.read_text(encoding="utf-8")

        self.assertIn("DROP INDEX unique_news_title", migration_sql)
        self.assertIn("unique_canonical_url_hash", migration_sql)


if __name__ == "__main__":
    unittest.main()
