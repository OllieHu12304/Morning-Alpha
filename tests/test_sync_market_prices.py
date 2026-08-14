"""測試每日價格缺漏日期的選擇與回補流程。"""

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import sync_market_prices  # noqa: E402


class SyncMarketPricesTests(unittest.TestCase):
    @patch("sync_market_prices.assess_market_data_freshness")
    @patch("sync_market_prices.fetch_missing_market_prices")
    @patch("sync_market_prices.get_expected_trade_date")
    @patch("sync_market_prices.save_market_prices")
    @patch("sync_market_prices.fetch_market_prices")
    def test_stale_snapshot_is_completed_by_current_historical_prices(
        self,
        mock_fetch_snapshot,
        mock_save_prices,
        mock_expected_date,
        mock_fetch_missing,
        mock_assess_freshness,
    ):
        snapshot_records = [{"trade_date": date(2026, 8, 13)}]
        historical_records = [{"trade_date": date(2026, 8, 14)}]
        mock_fetch_snapshot.return_value = snapshot_records
        mock_expected_date.return_value = date(2026, 8, 14)
        mock_fetch_missing.return_value = (
            historical_records,
            ["2026-08-14"],
        )
        mock_save_prices.side_effect = [
            {"source_count": 1, "saved_count": 1, "skipped_count": 0},
            {"source_count": 1, "saved_count": 1, "skipped_count": 0},
        ]
        mock_assess_freshness.return_value = {
            "latest_trade_date": "2026-08-14",
            "expected_trade_date": "2026-08-14",
            "is_stale": False,
            "availability_status": "available",
        }

        result = sync_market_prices.run()

        self.assertEqual(result["latest_trade_date"], "2026-08-14")
        self.assertEqual(result["backfilled_trade_dates"], ["2026-08-14"])
        self.assertEqual(mock_save_prices.call_count, 2)
        mock_assess_freshness.assert_called_once_with(
            snapshot_records + historical_records,
            expected_trade_date=date(2026, 8, 14),
        )

    def test_existing_history_only_fetches_dates_after_latest(self):
        summary = {
            "minimum_date": date(2026, 8, 10),
            "maximum_date": date(2026, 8, 11),
            "date_count": 2,
        }

        missing_dates = sync_market_prices.get_missing_market_dates(
            summary,
            {date(2026, 8, 11)},
            date(2026, 8, 12),
        )

        self.assertEqual(missing_dates, [date(2026, 8, 12)])

    def test_first_snapshot_backfills_recent_weekdays(self):
        summary = {
            "minimum_date": date(2026, 8, 12),
            "maximum_date": date(2026, 8, 12),
            "date_count": 1,
        }

        missing_dates = sync_market_prices.get_missing_market_dates(
            summary,
            {date(2026, 8, 12)},
            date(2026, 8, 12),
        )

        self.assertNotIn(date(2026, 8, 12), missing_dates)
        self.assertTrue(all(value.weekday() < 5 for value in missing_dates))
        self.assertGreater(len(missing_dates), 5)

    def test_old_database_never_requests_more_than_two_weeks(self):
        summary = {
            "minimum_date": date(2025, 1, 1),
            "maximum_date": date(2025, 1, 2),
            "date_count": 2,
        }

        missing_dates = sync_market_prices.get_missing_market_dates(
            summary,
            set(),
            date(2026, 8, 12),
        )

        self.assertGreaterEqual(missing_dates[0], date(2026, 7, 30))
        self.assertLessEqual(len(missing_dates), 10)

    @patch("sync_market_prices.fetch_historical_market_prices")
    @patch("sync_market_prices.load_market_date_state")
    def test_closed_dates_are_skipped_without_fake_records(
        self,
        mock_load_state,
        mock_fetch_history,
    ):
        mock_load_state.return_value = ({
            "minimum_date": date(2026, 8, 10),
            "maximum_date": date(2026, 8, 10),
            "date_count": 2,
        }, {date(2026, 8, 10)})
        mock_fetch_history.side_effect = [[], [{"trade_date": date(2026, 8, 12)}]]

        records, completed_dates = (
            sync_market_prices.fetch_missing_market_prices(date(2026, 8, 12))
        )

        self.assertEqual(records, [{"trade_date": date(2026, 8, 12)}])
        self.assertEqual(completed_dates, ["2026-08-12"])


if __name__ == "__main__":
    unittest.main()
