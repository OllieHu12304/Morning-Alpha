"""測試公司、產業與股票代號資料模型。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from company_directory import (  # noqa: E402
    COMPANY_DIRECTORY_TABLE_STATEMENTS,
    create_company_directory_tables,
    import_company_records,
)


class CompanyDirectoryTests(unittest.TestCase):
    def test_create_tables_uses_dependency_order(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value

        create_company_directory_tables(connection)

        executed_sql = [
            call.args[0]
            for call in cursor.execute.call_args_list
        ]
        self.assertEqual(len(executed_sql), 4)
        self.assertIn("CREATE TABLE IF NOT EXISTS industries", executed_sql[0])
        self.assertIn("CREATE TABLE IF NOT EXISTS companies", executed_sql[1])
        self.assertIn("CREATE TABLE IF NOT EXISTS securities", executed_sql[2])
        self.assertIn("CREATE TABLE IF NOT EXISTS company_aliases", executed_sql[3])

    def test_schema_defines_unique_ticker_and_alias(self):
        schema_sql = "\n".join(COMPANY_DIRECTORY_TABLE_STATEMENTS)

        self.assertIn("unique_security_exchange_ticker", schema_sql)
        self.assertIn("unique_company_alias", schema_sql)
        self.assertIn("foreign_company_industry", schema_sql)
        self.assertIn("foreign_security_company", schema_sql)

    def test_migration_matches_required_tables(self):
        migration_sql = (
            PROJECT_DIRECTORY / "sql" / "008_create_company_directory.sql"
        ).read_text(encoding="utf-8")

        for table_name in [
            "industries",
            "companies",
            "securities",
            "company_aliases",
        ]:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table_name}", migration_sql)

    def test_import_company_records_uses_parameterized_upserts(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.lastrowid = 7
        record = {
            "name": "台灣積體電路製造股份有限公司",
            "short_name": "台積電",
            "industry": "半導體業",
            "market": "TWSE",
            "ticker": "2330",
            "exchange": "TWSE",
            "currency": "TWD",
            "aliases": ["台積電", "台灣積體電路製造股份有限公司"],
        }

        imported_count = import_company_records(connection, [record])

        self.assertEqual(imported_count, 1)
        self.assertEqual(cursor.execute.call_count, 9)
        self.assertEqual(cursor.execute.call_args_list[4].args[1], ("半導體業",))
        self.assertEqual(cursor.execute.call_args_list[6].args[1][1], "2330")


if __name__ == "__main__":
    unittest.main()
