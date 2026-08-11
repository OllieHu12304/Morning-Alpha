"""測試市場與財務資料來源契約。"""

import sys
import unittest
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from market_data_contract import (  # noqa: E402
    FINANCIAL_COMMON_FIELDS,
    FINANCIAL_FIELD_MAP,
    FINANCIAL_SOURCE,
    MARKET_PRICE_COMMON_FIELDS,
    MARKET_PRICE_FIELD_MAP,
    MARKET_PRICE_SOURCE,
    find_missing_fields,
    validate_source_contract,
)


class MarketDataContractTests(unittest.TestCase):
    def test_sources_use_official_twse_https_api(self):
        for source in [MARKET_PRICE_SOURCE, FINANCIAL_SOURCE]:
            self.assertTrue(validate_source_contract(source))
            self.assertEqual(source["exchange"], "TWSE")
            self.assertEqual(source["currency"], "TWD")

    def test_price_contract_contains_identity_and_ohlcv_fields(self):
        expected_fields = {
            "ticker",
            "exchange",
            "trade_date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
            "source",
            "fetched_at",
        }

        self.assertTrue(expected_fields.issubset(MARKET_PRICE_COMMON_FIELDS))
        self.assertEqual(MARKET_PRICE_FIELD_MAP["Code"], "ticker")
        self.assertEqual(MARKET_PRICE_FIELD_MAP["Date"], "trade_date")

    def test_financial_contract_contains_period_and_summary_fields(self):
        expected_fields = {
            "ticker",
            "fiscal_year",
            "fiscal_quarter",
            "earnings_per_share",
            "operating_revenue",
            "operating_income",
            "net_income",
        }

        self.assertTrue(expected_fields.issubset(FINANCIAL_COMMON_FIELDS))
        self.assertEqual(FINANCIAL_FIELD_MAP["公司代號"], "ticker")
        self.assertEqual(
            FINANCIAL_FIELD_MAP["基本每股盈餘(元)"],
            "earnings_per_share",
        )

    def test_find_missing_fields_rejects_blank_values(self):
        missing_fields = find_missing_fields(
            {"Code": "2330", "Date": ""},
            ["Code", "Date", "ClosingPrice"],
        )

        self.assertEqual(missing_fields, ["Date", "ClosingPrice"])

    def test_document_explains_scope_and_limitations(self):
        document = (
            PROJECT_DIRECTORY / "docs" / "DATA_SOURCES.md"
        ).read_text(encoding="utf-8")

        self.assertIn("STOCK_DAY_ALL", document)
        self.assertIn("t187ap14_L", document)
        self.assertIn("目前不含 TPEx", document)
        self.assertIn("不構成投資建議", document)
        self.assertIn("不自行乘以千或萬", document)


if __name__ == "__main__":
    unittest.main()
