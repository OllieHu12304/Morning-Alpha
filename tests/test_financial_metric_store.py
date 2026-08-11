"""測試季度財務摘要的 MySQL 儲存準備流程。"""

import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
MIGRATION_PATH = (
    PROJECT_DIRECTORY / "sql" / "011_create_financial_metrics.sql"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from financial_metric_store import (  # noqa: E402
    prepare_financial_metric_rows,
    upsert_financial_metrics,
)


def create_record(ticker="2330"):
    return {
        "ticker": ticker,
        "exchange": "TWSE",
        "report_date": date(2026, 8, 11),
        "fiscal_year": 2026,
        "fiscal_quarter": 2,
        "industry": "半導體業",
        "earnings_per_share": Decimal("20.15"),
        "face_value_text": "新台幣 10.0000元",
        "operating_revenue": Decimal("1989254000.00"),
        "operating_income": Decimal("916800000.00"),
        "non_operating_income_expense": Decimal("35200000.00"),
        "net_income": Decimal("780300000.00"),
        "currency": "TWD",
        "source": "TWSE 上市公司各產業 EPS 統計資訊",
        "fetched_at": datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc),
    }


class FinancialMetricStoreTests(unittest.TestCase):
    def test_prepare_rows_maps_security_without_rescaling_values(self):
        rows, skipped_count = prepare_financial_metric_rows(
            [create_record()],
            {("TWSE", "2330"): 9},
        )

        self.assertEqual(skipped_count, 0)
        self.assertEqual(rows[0][0], 9)
        self.assertEqual(rows[0][2:4], (2026, 2))
        self.assertEqual(rows[0][7], Decimal("1989254000.00"))
        self.assertEqual(rows[0][-1], datetime(2026, 8, 11, 8, 0))

    def test_prepare_rows_skips_unknown_security(self):
        rows, skipped_count = prepare_financial_metric_rows(
            [create_record(ticker="9999")],
            {("TWSE", "2330"): 9},
        )

        self.assertEqual(rows, [])
        self.assertEqual(skipped_count, 1)

    @patch("financial_metric_store.fetch_security_ids")
    @patch("financial_metric_store.create_financial_metrics_table")
    def test_upsert_financial_metrics_uses_parameterized_rows(
        self,
        mock_create_table,
        mock_fetch_security_ids,
    ):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        mock_fetch_security_ids.return_value = {("TWSE", "2330"): 9}

        result = upsert_financial_metrics(connection, [create_record()])

        self.assertEqual(result, {
            "source_count": 1,
            "saved_count": 1,
            "skipped_count": 0,
        })
        cursor.executemany.assert_called_once()
        parameters = cursor.executemany.call_args.args[1]
        self.assertEqual(parameters[0][0], 9)
        mock_create_table.assert_called_once_with(connection)

    def test_migration_defines_unique_security_fiscal_period(self):
        migration = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS financial_metrics", migration)
        self.assertIn("UNIQUE KEY unique_security_fiscal_period", migration)
        self.assertIn("FOREIGN KEY (security_id)", migration)


if __name__ == "__main__":
    unittest.main()
