"""測試公司市場與財務 API 的資料轉換與查詢限制。"""

import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from company_market_data import (  # noqa: E402
    build_records,
    fetch_company_market_prices,
    fetch_market_companies,
    validate_limit,
)


class CompanyMarketDataTests(unittest.TestCase):
    def test_build_records_serializes_decimal_and_dates(self):
        rows = [(
            date(2026, 8, 11),
            Decimal("885.2500"),
            datetime(2026, 8, 11, 8, 30),
        )]
        columns = ["trade_date", "close_price", "fetched_at"]

        records = build_records(rows, columns)

        self.assertEqual(records[0], {
            "trade_date": "2026-08-11",
            "close_price": 885.25,
            "fetched_at": "2026-08-11T08:30:00",
        })

    def test_fetch_market_companies_converts_flags_to_boolean(self):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = [(
            8,
            "台灣積體電路製造股份有限公司",
            "台積電",
            "半導體業",
            "2330",
            "TWSE",
            1,
            0,
        )]
        cursor.description = [
            ("company_id",),
            ("name",),
            ("short_name",),
            ("industry",),
            ("ticker",),
            ("exchange",),
            ("has_market_prices",),
            ("has_financial_metrics",),
        ]
        connection.cursor.return_value.__enter__.return_value = cursor

        records = fetch_market_companies(connection)

        self.assertIs(records[0]["has_market_prices"], True)
        self.assertIs(records[0]["has_financial_metrics"], False)

    def test_market_price_query_uses_company_and_limit_parameters(self):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.description = [("trade_date",)]
        connection.cursor.return_value.__enter__.return_value = cursor

        records = fetch_company_market_prices(connection, 8, limit=30)

        self.assertEqual(records, [])
        self.assertEqual(cursor.execute.call_args.args[1], (8, 30))

    def test_validate_limit_rejects_unbounded_queries(self):
        with self.assertRaisesRegex(ValueError, "1 到 365"):
            validate_limit(1000)


if __name__ == "__main__":
    unittest.main()
