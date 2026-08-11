"""使用固定 fixture 測試 TWSE 公司資料 adapter。"""

import sys
import unittest
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"
FIXTURE_PATH = PROJECT_DIRECTORY / "tests" / "fixtures" / "twse_companies.json"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from twse_company_adapter import parse_companies  # noqa: E402


class TwseCompanyAdapterTests(unittest.TestCase):
    def test_parse_companies_returns_common_records(self):
        companies = parse_companies(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(len(companies), 2)
        self.assertEqual(companies[0], {
            "name": "台灣積體電路製造股份有限公司",
            "short_name": "台積電",
            "industry": "半導體業",
            "market": "TWSE",
            "ticker": "2330",
            "exchange": "TWSE",
            "currency": "TWD",
            "aliases": ["台積電", "台灣積體電路製造股份有限公司"],
        })

    def test_parse_companies_rejects_invalid_json(self):
        with self.assertRaisesRegex(ValueError, "有效 JSON"):
            parse_companies("not-json")

    def test_parse_companies_rejects_empty_list(self):
        with self.assertRaisesRegex(ValueError, "非空 list"):
            parse_companies("[]")


if __name__ == "__main__":
    unittest.main()
