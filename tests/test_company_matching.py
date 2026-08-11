"""測試新聞標題的可解釋公司實體辨識。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from company_matching import (  # noqa: E402
    match_news_records,
    match_title_companies,
)


def make_candidate(
    company_id=1,
    name="台灣積體電路製造股份有限公司",
    short_name="台積電",
    ticker="2330",
    aliases=None,
):
    if aliases is None:
        aliases = [short_name, name]

    return {
        "company_id": company_id,
        "name": name,
        "short_name": short_name,
        "industry": "半導體業",
        "ticker": ticker,
        "exchange": "TWSE",
        "aliases": aliases,
    }


class CompanyMatchingTests(unittest.TestCase):
    def test_matches_company_alias(self):
        matches = match_title_companies(
            "台積電先進製程持續成長",
            [make_candidate()],
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["company_id"], 1)
        self.assertEqual(matches[0]["match_method"], "alias")
        self.assertEqual(matches[0]["confidence"], 0.9)

    def test_matches_independent_ticker(self):
        matches = match_title_companies(
            "2330 今日召開法人說明會",
            [make_candidate()],
        )

        self.assertEqual(matches[0]["match_method"], "ticker")
        self.assertEqual(matches[0]["confidence"], 1.0)

    def test_ticker_does_not_match_inside_larger_number(self):
        matches = match_title_companies(
            "成交量達 12330 張",
            [make_candidate(aliases=[])],
        )

        self.assertEqual(matches, [])

    def test_keeps_only_best_match_for_same_company(self):
        matches = match_title_companies(
            "台灣積體電路製造股份有限公司（2330）公布結果",
            [make_candidate()],
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["match_method"], "company_name")

    def test_skips_alias_shared_by_multiple_companies(self):
        first = make_candidate(aliases=["中華"])
        second = make_candidate(
            company_id=2,
            name="中華電信股份有限公司",
            short_name="中華電",
            ticker="2412",
            aliases=["中華"],
        )

        matches = match_title_companies("中華公布最新消息", [first, second])

        self.assertEqual(matches, [])

    def test_match_news_records_does_not_modify_original(self):
        records = [{"title": "台積電營收成長"}]

        matched_records = match_news_records(records, [make_candidate()])

        self.assertNotIn("company_matches", records[0])
        self.assertEqual(len(matched_records[0]["company_matches"]), 1)


if __name__ == "__main__":
    unittest.main()
