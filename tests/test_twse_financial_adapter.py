"""使用固定 fixture 測試 TWSE 季度財務 adapter。"""

import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
FIXTURE_PATH = (
    PROJECT_DIRECTORY / "tests" / "fixtures" / "twse_financial_metrics.json"
)
sys.path.insert(0, str(SOURCE_DIRECTORY))

from twse_financial_adapter import (  # noqa: E402
    parse_financial_records,
    parse_fiscal_quarter,
    parse_fiscal_year,
)


class TwseFinancialAdapterTests(unittest.TestCase):
    def test_parse_financial_records_returns_common_records(self):
        fetched_at = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)

        records = parse_financial_records(
            FIXTURE_PATH.read_text(encoding="utf-8"),
            fetched_at=fetched_at,
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["ticker"], "2330")
        self.assertEqual(records[0]["report_date"], date(2026, 8, 11))
        self.assertEqual(records[0]["fiscal_year"], 2026)
        self.assertEqual(records[0]["fiscal_quarter"], 2)
        self.assertEqual(records[0]["earnings_per_share"], Decimal("20.15"))
        self.assertEqual(
            records[0]["operating_revenue"],
            Decimal("1989254000.00"),
        )
        self.assertEqual(records[0]["currency"], "TWD")
        self.assertEqual(records[0]["fetched_at"], fetched_at)

    def test_empty_financial_values_become_none(self):
        records = parse_financial_records(
            FIXTURE_PATH.read_text(encoding="utf-8"),
        )

        self.assertIsNone(records[1]["earnings_per_share"])
        self.assertIsNone(records[1]["operating_revenue"])
        self.assertIsNone(records[1]["net_income"])

    def test_fiscal_period_converts_and_validates(self):
        self.assertEqual(parse_fiscal_year("115"), 2026)
        self.assertEqual(parse_fiscal_quarter("4"), 4)

        with self.assertRaisesRegex(ValueError, "季別"):
            parse_fiscal_quarter("5")

    def test_parse_financial_records_detects_structure_change(self):
        invalid_json = '[{"出表日期": "1150811", "公司代號": "2330"}]'

        with self.assertRaisesRegex(ValueError, "結構異常"):
            parse_financial_records(invalid_json)

    def test_parse_financial_records_rejects_naive_fetched_at(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_financial_records(
                FIXTURE_PATH.read_text(encoding="utf-8"),
                fetched_at=datetime(2026, 8, 11, 8, 0),
            )


if __name__ == "__main__":
    unittest.main()
