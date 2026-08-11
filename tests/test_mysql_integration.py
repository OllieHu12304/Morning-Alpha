"""在獨立 morning_alpha_test database 驗證真實 MySQL 行為。"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from store_news import (  # noqa: E402
    connect_to_database,
    create_news_table,
    insert_news_records,
    load_environment,
)
from source_health import (  # noqa: E402
    build_source_health_summary,
    create_source_health_table,
    fetch_source_health_events,
    insert_source_health_events,
)


TEST_DATABASE_NAME = "morning_alpha_test"
load_environment()
RUN_INTEGRATION_TESTS = os.getenv("RUN_MYSQL_INTEGRATION") == "1"


def get_test_database_config():
    """讀取測試專用設定，並拒絕任何非測試 database。"""
    user = os.getenv("MYSQL_TEST_USER")
    password = os.getenv("MYSQL_TEST_PASSWORD")
    database = os.getenv("MYSQL_TEST_DATABASE", TEST_DATABASE_NAME)

    if not user or not password:
        raise ValueError(
            "請設定 MYSQL_TEST_USER 與 MYSQL_TEST_PASSWORD。"
        )

    if database != TEST_DATABASE_NAME:
        raise ValueError(
            f"Integration tests 只允許使用 {TEST_DATABASE_NAME}。"
        )

    try:
        port = int(os.getenv("MYSQL_TEST_PORT", "3306"))
    except ValueError as error:
        raise ValueError("MYSQL_TEST_PORT 必須是整數。") from error

    return {
        "host": os.getenv("MYSQL_TEST_HOST", "localhost"),
        "port": port,
        "user": user,
        "password": password,
        "database": database,
    }


def create_news_dataframe(title, url):
    """建立一筆 integration test 使用的新聞。"""
    return pd.DataFrame([{
        "source": "integration_test",
        "source_category": None,
        "title": title,
        "publish_time": pd.Timestamp("2026-08-11 10:00:00"),
        "url": url,
    }])


class MySQLIntegrationSafetyTests(unittest.TestCase):
    def test_config_rejects_production_database_name(self):
        test_environment = {
            "MYSQL_TEST_USER": "test_user",
            "MYSQL_TEST_PASSWORD": "test_password",
            "MYSQL_TEST_DATABASE": "morning_alpha",
        }

        with patch.dict(os.environ, test_environment, clear=True):
            with self.assertRaisesRegex(ValueError, "只允許"):
                get_test_database_config()


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "設定 RUN_MYSQL_INTEGRATION=1 才執行真實 MySQL tests。",
)
class MySQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = get_test_database_config()
        cls.connection = connect_to_database(config)
        create_news_table(cls.connection)
        create_source_health_table(cls.connection)
        cls.connection.commit()

    @classmethod
    def tearDownClass(cls):
        cls.clear_test_records()
        cls.connection.close()

    @classmethod
    def clear_test_records(cls):
        """只清空已驗證名稱的 integration test table。"""
        with cls.connection.cursor() as cursor:
            cursor.execute("DELETE FROM source_health_events;")
            cursor.execute("DELETE FROM news_records;")

        cls.connection.commit()

    def setUp(self):
        self.clear_test_records()

    def tearDown(self):
        self.clear_test_records()

    def test_insert_and_read_news_record(self):
        dataframe = create_news_dataframe(
            "人工智慧 integration test 新聞",
            "https://example.com/integration-news/",
        )

        inserted_count = insert_news_records(self.connection, dataframe)
        self.connection.commit()

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source, analysis_category, title, canonical_url
                FROM news_records;
                """
            )
            record = cursor.fetchone()

        self.assertEqual(inserted_count, 1)
        self.assertEqual(record, (
            "integration_test",
            "AI 與人工智慧",
            "人工智慧 integration test 新聞",
            "https://example.com/integration-news/",
        ))

    def test_canonical_url_unique_index_ignores_duplicate(self):
        first_dataframe = create_news_dataframe(
            "第一篇測試新聞",
            "https://example.com/same-news/?utm_source=first",
        )
        second_dataframe = create_news_dataframe(
            "標題不同但網址相同",
            "https://example.com/same-news/?utm_source=second",
        )

        first_count = insert_news_records(
            self.connection,
            first_dataframe,
        )
        second_count = insert_news_records(
            self.connection,
            second_dataframe,
        )
        self.connection.commit()

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM news_records;")
            record_count = cursor.fetchone()[0]

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        self.assertEqual(record_count, 1)

    def test_insert_and_read_source_health_event(self):
        inserted_count = insert_source_health_events(
            self.connection,
            [{
                "source": "integration_test",
                "status": "failure",
                "article_count": 0,
                "error_message": "HTTP 503",
            }],
        )
        self.connection.commit()

        rows, columns = fetch_source_health_events(self.connection)
        summaries = build_source_health_summary(rows, columns)

        self.assertEqual(inserted_count, 1)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["source"], "integration_test")
        self.assertEqual(summaries[0]["status"], "failure")
        self.assertEqual(summaries[0]["error_message"], "HTTP 503")


if __name__ == "__main__":
    unittest.main()
