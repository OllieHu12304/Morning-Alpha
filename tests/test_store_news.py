"""測試新聞資料寫入 MySQL 前的準備邏輯與 schema。"""

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import store_news  # noqa: E402


class StoreNewsTests(unittest.TestCase):
    def test_prepare_news_records_adds_source_and_canonical_url(self):
        dataframe = pd.DataFrame([{
            "title": "測試新聞",
            "publish_time": pd.Timestamp("2026-08-11 09:30:00"),
            "url": "https://technews.tw/example/",
        }])

        records = store_news.prepare_news_records(dataframe)

        self.assertEqual(records, [(
            "technews",
            "測試新聞",
            pd.Timestamp("2026-08-11 09:30:00").to_pydatetime(),
            "https://technews.tw/example/",
            "https://technews.tw/example/",
        )])

    def test_prepare_news_records_rejects_missing_title(self):
        dataframe = pd.DataFrame([{
            "title": "",
            "publish_time": pd.Timestamp("2026-08-11 09:30:00"),
            "url": "https://technews.tw/example/",
        }])

        with self.assertRaisesRegex(ValueError, "空白欄位"):
            store_news.prepare_news_records(dataframe)

    def test_prepare_news_records_rejects_invalid_publish_time(self):
        dataframe = pd.DataFrame([{
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

    def test_insert_sql_writes_source_and_canonical_url(self):
        sql = store_news.INSERT_NEWS_SQL

        self.assertIn("source", sql)
        self.assertIn("canonical_url", sql)
        self.assertEqual(sql.count("%s"), 5)

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


if __name__ == "__main__":
    unittest.main()
