"""測試 TWSE 每日價格的 MySQL 儲存準備流程。"""

import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
MIGRATION_PATH = (
    PROJECT_DIRECTORY / "sql" / "010_create_market_prices.sql"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from market_price_store import (  # noqa: E402
    fetch_market_date_summary,
    fetch_market_dates,
    prepare_market_price_rows,
    upsert_market_prices,
)


def create_record(ticker="2330"):
    return {
        "ticker": ticker,
        "exchange": "TWSE",
        "trade_date": date(2026, 8, 11),
        "open_price": Decimal("880.00"),
        "high_price": Decimal("890.00"),
        "low_price": Decimal("875.00"),
        "close_price": Decimal("885.00"),
        "price_change": Decimal("5.00"),
        "volume": 25000000,
        "trade_value": Decimal("22125000000"),
        "transaction_count": 45000,
        "source": "TWSE 上市個股日成交資訊",
        "fetched_at": datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc),
    }


class MarketPriceStoreTests(unittest.TestCase):
    def test_market_date_queries_return_summary_and_dates(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = (
            date(2026, 8, 11),
            date(2026, 8, 12),
            2,
        )

        summary = fetch_market_date_summary(connection)

        self.assertEqual(summary["date_count"], 2)
        cursor.fetchall.return_value = [
            (date(2026, 8, 11),),
            (date(2026, 8, 12),),
        ]
        dates = fetch_market_dates(
            connection,
            date(2026, 8, 11),
            date(2026, 8, 12),
        )
        self.assertEqual(dates, {date(2026, 8, 11), date(2026, 8, 12)})
    def test_prepare_rows_maps_security_and_converts_utc_time(self):
        rows, skipped_count = prepare_market_price_rows(
            [create_record()],
            {("TWSE", "2330"): 9},
        )

        self.assertEqual(skipped_count, 0)
        self.assertEqual(rows[0][0], 9)
        self.assertEqual(rows[0][1], date(2026, 8, 11))
        self.assertEqual(rows[0][-1], datetime(2026, 8, 11, 8, 0))

    def test_prepare_rows_skips_unknown_security(self):
        rows, skipped_count = prepare_market_price_rows(
            [create_record(ticker="00940")],
            {("TWSE", "2330"): 9},
        )

        self.assertEqual(rows, [])
        self.assertEqual(skipped_count, 1)

    @patch("market_price_store.fetch_security_ids")
    @patch("market_price_store.create_market_prices_table")
    def test_upsert_market_prices_uses_parameterized_rows(
        self,
        mock_create_table,
        mock_fetch_security_ids,
    ):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        mock_fetch_security_ids.return_value = {("TWSE", "2330"): 9}

        result = upsert_market_prices(connection, [create_record()])

        self.assertEqual(result, {
            "source_count": 1,
            "saved_count": 1,
            "skipped_count": 0,
        })
        cursor.executemany.assert_called_once()
        parameters = cursor.executemany.call_args.args[1]
        self.assertEqual(parameters[0][0], 9)
        mock_create_table.assert_called_once_with(connection)

    def test_migration_defines_unique_daily_security_price(self):
        migration = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("CREATE TABLE IF NOT EXISTS market_prices", migration)
        self.assertIn("UNIQUE KEY unique_security_trade_date", migration)
        self.assertIn("FOREIGN KEY (security_id)", migration)


if __name__ == "__main__":
    unittest.main()
