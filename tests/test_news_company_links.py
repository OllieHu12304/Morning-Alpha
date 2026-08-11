"""測試新聞公司關聯的同步與 API 資料轉換。"""

import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from news_company_links import (  # noqa: E402
    build_news_company_link_records,
    fetch_news_company_links,
    replace_news_links,
    sync_news_company_links,
)


class NewsCompanyLinksTests(unittest.TestCase):
    def test_replace_news_links_deletes_old_links_before_inserting(self):
        cursor = MagicMock()
        matches = [{
            "company_id": 9,
            "matched_text": "台積電",
            "match_method": "alias",
            "confidence": 0.9,
        }]

        replace_news_links(cursor, 3, matches)

        self.assertEqual(cursor.execute.call_count, 2)
        delete_parameters = cursor.execute.call_args_list[0].args[1]
        insert_parameters = cursor.execute.call_args_list[1].args[1]
        self.assertEqual(delete_parameters, (3,))
        self.assertEqual(insert_parameters, (3, 9, "台積電", "alias", 0.9))

    @patch("news_company_links.fetch_news_titles")
    @patch("news_company_links.fetch_company_candidates")
    @patch("news_company_links.create_news_company_links_table")
    def test_sync_news_company_links_returns_counts(
        self,
        mock_create_table,
        mock_fetch_candidates,
        mock_fetch_news,
    ):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        mock_fetch_candidates.return_value = [{
            "company_id": 9,
            "name": "台灣積體電路製造股份有限公司",
            "short_name": "台積電",
            "industry": "半導體業",
            "ticker": "2330",
            "exchange": "TWSE",
            "aliases": ["台積電"],
        }]
        mock_fetch_news.return_value = [
            {"news_id": 3, "title": "台積電公布最新營收"},
            {"news_id": 4, "title": "今日天氣預報"},
        ]

        result = sync_news_company_links(connection)

        self.assertEqual(result, {"news_count": 2, "link_count": 1})
        self.assertEqual(cursor.execute.call_count, 3)
        mock_create_table.assert_called_once_with(connection)

    def test_build_records_converts_decimal_confidence(self):
        rows = [(3, 9, "台積電", Decimal("0.900"))]
        columns = ["news_id", "company_id", "name", "confidence"]

        records = build_news_company_link_records(rows, columns)

        self.assertEqual(records[0]["confidence"], 0.9)

    def test_fetch_links_uses_parameterized_company_filter(self):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.description = [
            ("news_id",),
            ("company_id",),
            ("confidence",),
        ]
        connection.cursor.return_value.__enter__.return_value = cursor

        records = fetch_news_company_links(connection, company_id=9)

        self.assertEqual(records, [])
        query, parameters = cursor.execute.call_args.args
        self.assertIn("WHERE news_company_links.company_id = %s", query)
        self.assertEqual(parameters, (9,))


if __name__ == "__main__":
    unittest.main()
