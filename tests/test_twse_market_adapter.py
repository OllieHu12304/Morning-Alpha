"""使用固定 fixture 測試 TWSE 每日價格 adapter。"""

import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
FIXTURE_PATH = (
    PROJECT_DIRECTORY / "tests" / "fixtures" / "twse_market_prices.json"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from twse_market_adapter import (  # noqa: E402
    assess_market_data_freshness,
    get_expected_trade_date,
    parse_market_prices,
    parse_roc_date,
)


class TwseMarketAdapterTests(unittest.TestCase):
    def test_expected_trade_date_uses_previous_friday_on_monday_morning(self):
        current_time = datetime(2026, 8, 17, 1, 0, tzinfo=timezone.utc)

        self.assertEqual(
            get_expected_trade_date(current_time),
            date(2026, 8, 14),
        )

    def test_freshness_reports_official_data_behind_expected_date(self):
        records = [{"trade_date": date(2026, 8, 11)}]
        current_time = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)

        status = assess_market_data_freshness(records, current_time)

        self.assertEqual(status["latest_trade_date"], "2026-08-11")
        self.assertEqual(status["expected_trade_date"], "2026-08-12")
        self.assertTrue(status["is_stale"])

    def test_parse_market_prices_returns_common_records(self):
        fetched_at = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)

        records = parse_market_prices(
            FIXTURE_PATH.read_text(encoding="utf-8"),
            fetched_at=fetched_at,
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["ticker"], "2330")
        self.assertEqual(records[0]["trade_date"], date(2026, 8, 11))
        self.assertEqual(records[0]["open_price"], Decimal("880.00"))
        self.assertEqual(records[0]["price_change"], Decimal("+5.00"))
        self.assertEqual(records[0]["volume"], 25000000)
        self.assertEqual(records[0]["transaction_count"], 45000)
        self.assertEqual(records[0]["exchange"], "TWSE")
        self.assertEqual(records[0]["currency"], "TWD")
        self.assertEqual(records[0]["fetched_at"], fetched_at)

    def test_empty_prices_become_none_not_zero(self):
        records = parse_market_prices(
            FIXTURE_PATH.read_text(encoding="utf-8"),
        )

        self.assertIsNone(records[1]["open_price"])
        self.assertIsNone(records[1]["close_price"])
        self.assertEqual(records[1]["volume"], 0)

    def test_parse_roc_date_converts_to_gregorian_date(self):
        self.assertEqual(parse_roc_date("1150811"), date(2026, 8, 11))

    def test_parse_market_prices_detects_structure_change(self):
        invalid_json = '[{"Date": "1150811", "Code": "2330"}]'

        with self.assertRaisesRegex(ValueError, "結構異常"):
            parse_market_prices(invalid_json)

    def test_parse_market_prices_rejects_naive_fetched_at(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_market_prices(
                FIXTURE_PATH.read_text(encoding="utf-8"),
                fetched_at=datetime(2026, 8, 11, 8, 0),
            )


if __name__ == "__main__":
    unittest.main()
