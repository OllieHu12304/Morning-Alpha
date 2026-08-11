"""測試 MySQL migration runner 的安全判斷。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from run_migrations import (  # noqa: E402
    get_migration_status,
    split_sql_statements,
    validate_schema_state,
)


class RunMigrationsTests(unittest.TestCase):
    def test_get_migration_status_recognizes_latest_schema(self):
        schema_state = {
            "table_exists": True,
            "columns": {
                "id",
                "source",
                "source_category",
                "analysis_category",
                "canonical_url",
                "canonical_url_hash",
            },
            "indexes": {
                "PRIMARY",
                "unique_canonical_url_hash",
            },
            "source_health_exists": True,
            "pipeline_runs_exists": True,
            "daily_briefs_exists": True,
            "company_directory_exists": True,
            "news_company_links_exists": True,
        }

        self.assertEqual(get_migration_status(schema_state), {
            "001": True,
            "002": True,
            "003": True,
            "004": True,
            "005": True,
            "006": True,
            "007": True,
            "008": True,
            "009": True,
        })

    def test_get_migration_status_detects_partially_updated_schema(self):
        schema_state = {
            "table_exists": True,
            "columns": {
                "source",
                "source_category",
                "analysis_category",
                "canonical_url",
            },
            "indexes": {"PRIMARY", "unique_news_title"},
            "source_health_exists": False,
            "pipeline_runs_exists": False,
            "daily_briefs_exists": False,
            "company_directory_exists": False,
            "news_company_links_exists": False,
        }

        self.assertEqual(get_migration_status(schema_state), {
            "001": True,
            "002": False,
            "003": False,
            "004": False,
            "005": False,
            "006": False,
            "007": False,
            "008": False,
            "009": False,
        })

    def test_split_sql_statements_removes_comment_lines(self):
        sql_text = """
        -- 說明文字
        ALTER TABLE news_records ADD COLUMN test_value INT;

        SELECT COUNT(*) FROM news_records;
        """

        statements = split_sql_statements(sql_text)

        self.assertEqual(len(statements), 2)
        self.assertTrue(statements[0].startswith("ALTER TABLE"))
        self.assertTrue(statements[1].startswith("SELECT COUNT"))

    def test_validate_schema_state_rejects_partial_quality_fields(self):
        schema_state = {
            "table_exists": True,
            "columns": {"id", "source", "source_category"},
            "indexes": {"PRIMARY"},
        }

        with self.assertRaisesRegex(ValueError, "部分"):
            validate_schema_state(schema_state)


if __name__ == "__main__":
    unittest.main()
