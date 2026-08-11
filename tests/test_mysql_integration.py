"""在獨立 morning_alpha_test database 驗證真實 MySQL 行為。"""

import os
import sys
import unittest
from datetime import datetime
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
from pipeline_history import (  # noqa: E402
    build_pipeline_run_records,
    create_pending_step_results,
    create_pipeline_runs_table,
    fetch_pipeline_runs,
    insert_pipeline_run,
    update_step_result,
)
from history_retention import delete_old_history  # noqa: E402
from daily_brief_store import (  # noqa: E402
    create_daily_briefs_table,
    fetch_daily_briefs,
    upsert_daily_brief,
)
from company_directory import create_company_directory_tables  # noqa: E402


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


def create_successful_step_results():
    """建立 integration tests 共用的成功步驟 JSON。"""
    step_results = create_pending_step_results()

    for step_result in step_results:
        update_step_result(
            step_results,
            step_result["step"],
            "success",
            10,
            {"count": 1},
        )

    return step_results


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
        create_pipeline_runs_table(cls.connection)
        create_daily_briefs_table(cls.connection)
        create_company_directory_tables(cls.connection)
        cls.connection.commit()

    @classmethod
    def tearDownClass(cls):
        cls.clear_test_records()
        cls.connection.close()

    @classmethod
    def clear_test_records(cls):
        """只清空已驗證名稱的 integration test table。"""
        with cls.connection.cursor() as cursor:
            cursor.execute("DELETE FROM company_aliases;")
            cursor.execute("DELETE FROM securities;")
            cursor.execute("DELETE FROM companies;")
            cursor.execute("DELETE FROM industries;")
            cursor.execute("DELETE FROM daily_briefs;")
            cursor.execute("DELETE FROM pipeline_runs;")
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

    def test_insert_and_read_pipeline_run(self):
        step_results = create_successful_step_results()

        inserted_id = insert_pipeline_run(self.connection, {
            "status": "success",
            "started_at": datetime(2026, 8, 11, 10, 0, 0),
            "finished_at": datetime(2026, 8, 11, 10, 0, 1),
            "duration_ms": 1000,
            "failed_step": None,
            "step_results": step_results,
            "error_message": None,
        })
        self.connection.commit()

        rows, columns = fetch_pipeline_runs(self.connection, limit=10)
        records = build_pipeline_run_records(rows, columns)

        self.assertGreater(inserted_id, 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "success")
        self.assertEqual(len(records[0]["step_results"]), 4)

    def test_upsert_and_read_daily_brief(self):
        brief = {
            "brief_date": "2026-08-12",
            "window_start": "2026-08-11T07:00:00+08:00",
            "window_end": "2026-08-12T07:00:00+08:00",
            "article_count": 1,
            "summary": "integration test 晨報",
            "sources": [],
            "categories": [],
            "keywords": [],
            "highlights": [],
            "limitations": [],
        }

        upsert_daily_brief(self.connection, brief)
        self.connection.commit()
        records = fetch_daily_briefs(self.connection, limit=10)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["brief_date"], "2026-08-12")
        self.assertEqual(records[0]["summary"], "integration test 晨報")

    def test_company_directory_foreign_keys(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO industries (name) VALUES (%s);",
                ("半導體業",),
            )
            industry_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO companies (name, short_name, industry_id, market)
                VALUES (%s, %s, %s, %s);
                """,
                ("台灣積體電路製造股份有限公司", "台積電", industry_id, "TWSE"),
            )
            company_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO securities (company_id, ticker, exchange, currency)
                VALUES (%s, %s, %s, %s);
                """,
                (company_id, "2330", "TWSE", "TWD"),
            )
            cursor.execute(
                "INSERT INTO company_aliases (company_id, alias) VALUES (%s, %s);",
                (company_id, "台積電"),
            )

        self.connection.commit()

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT companies.short_name, securities.ticker, industries.name
                FROM companies
                JOIN securities ON securities.company_id = companies.id
                JOIN industries ON industries.id = companies.industry_id;
                """
            )
            record = cursor.fetchone()

        self.assertEqual(record, ("台積電", "2330", "半導體業"))

    def test_history_retention_deletes_only_old_records(self):
        old_time = datetime(2026, 1, 1, 0, 0, 0)
        recent_time = datetime(2026, 8, 10, 0, 0, 0)
        cutoff = datetime(2026, 8, 1, 0, 0, 0)

        with self.connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO source_health_events (
                    source,
                    status,
                    article_count,
                    error_message,
                    attempted_at
                )
                VALUES (%s, %s, %s, %s, %s);
                """,
                [
                    ("old_source", "success", 1, None, old_time),
                    ("recent_source", "success", 1, None, recent_time),
                ],
            )

        for started_at in [old_time, recent_time]:
            insert_pipeline_run(self.connection, {
                "status": "success",
                "started_at": started_at,
                "finished_at": started_at,
                "duration_ms": 0,
                "failed_step": None,
                "step_results": create_successful_step_results(),
                "error_message": None,
            })

        deleted_counts = delete_old_history(self.connection, cutoff)
        self.connection.commit()

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM source_health_events;")
            source_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM pipeline_runs;")
            pipeline_count = cursor.fetchone()[0]

        self.assertEqual(deleted_counts, {
            "source_health_events": 1,
            "pipeline_runs": 1,
        })
        self.assertEqual(source_count, 1)
        self.assertEqual(pipeline_count, 1)


if __name__ == "__main__":
    unittest.main()
