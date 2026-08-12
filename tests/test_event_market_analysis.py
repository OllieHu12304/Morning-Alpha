"""測試新聞事件與市場價格的保守時間關聯。"""

import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from event_market_analysis import (  # noqa: E402
    ANALYSIS_TYPE,
    LIMITATIONS,
    build_event_market_observation,
    create_event_market_observations,
    fetch_event_candidates,
    fetch_event_market_readiness,
    select_observation_window,
)


def create_candidate(publish_time):
    return {
        "title": "台積電測試新聞",
        "publish_time": publish_time,
        "url": "https://example.com/news/1",
        "source": "test",
        "company_id": 8,
        "company_name": "台灣積體電路製造股份有限公司",
        "short_name": "台積電",
        "security_id": 9,
        "ticker": "2330",
        "exchange": "TWSE",
        "match_confidence": Decimal("0.900"),
    }


def create_prices():
    return [
        {"trade_date": date(2026, 8, 7), "close_price": Decimal("880")},
        {"trade_date": date(2026, 8, 10), "close_price": Decimal("890")},
        {"trade_date": date(2026, 8, 11), "close_price": Decimal("900")},
    ]


class EventMarketAnalysisTests(unittest.TestCase):
    def test_candidate_query_accepts_expanded_search_limit(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = []
        cursor.description = [("title",)]

        records = fetch_event_candidates(connection, 400)

        self.assertEqual(records, [])
        self.assertEqual(cursor.execute.call_args.args[1], (400,))

    def test_readiness_explains_available_links_and_price_dates(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = (
            12,
            3,
            date(2026, 8, 10),
            date(2026, 8, 12),
        )

        readiness = fetch_event_market_readiness(connection)

        self.assertEqual(readiness["candidate_count"], 12)
        self.assertEqual(readiness["price_date_count"], 3)
        self.assertEqual(readiness["latest_trade_date"], "2026-08-12")

    def test_before_close_observes_same_trading_day(self):
        window = select_observation_window(
            datetime(2026, 8, 10, 10, 0),
            create_prices(),
        )

        self.assertEqual(window[0]["trade_date"], date(2026, 8, 7))
        self.assertEqual(window[1]["trade_date"], date(2026, 8, 10))

    def test_after_close_observes_next_trading_day(self):
        window = select_observation_window(
            datetime(2026, 8, 10, 15, 0),
            create_prices(),
        )

        self.assertEqual(window[0]["trade_date"], date(2026, 8, 10))
        self.assertEqual(window[1]["trade_date"], date(2026, 8, 11))

    def test_exact_close_time_uses_next_trading_day(self):
        window = select_observation_window(
            datetime(2026, 8, 10, 13, 30),
            create_prices(),
        )

        self.assertEqual(window[1]["trade_date"], date(2026, 8, 11))

    def test_weekend_uses_next_available_trading_day(self):
        window = select_observation_window(
            datetime(2026, 8, 8, 10, 0),
            create_prices(),
        )

        self.assertEqual(window[1]["trade_date"], date(2026, 8, 10))

    def test_build_observation_calculates_change_and_labels_limit(self):
        observation = build_event_market_observation(
            create_candidate(datetime(2026, 8, 10, 10, 0)),
            create_prices(),
        )

        self.assertEqual(observation["analysis_type"], ANALYSIS_TYPE)
        self.assertEqual(observation["price_change"], 10.0)
        self.assertEqual(observation["change_percent"], 1.1364)
        self.assertIn("不代表", LIMITATIONS[0])

    def test_missing_previous_price_returns_no_observation(self):
        prices = [{
            "trade_date": date(2026, 8, 10),
            "close_price": Decimal("890"),
        }]

        observation = build_event_market_observation(
            create_candidate(datetime(2026, 8, 10, 10, 0)),
            prices,
        )

        self.assertIsNone(observation)

    @patch("event_market_analysis.fetch_security_prices")
    @patch("event_market_analysis.fetch_event_candidates")
    def test_create_observations_caches_prices_by_security(
        self,
        mock_fetch_candidates,
        mock_fetch_prices,
    ):
        first = create_candidate(datetime(2026, 8, 10, 10, 0))
        second = create_candidate(datetime(2026, 8, 10, 11, 0))
        second["title"] = "第二則台積電測試新聞"
        mock_fetch_candidates.return_value = [first, second]
        mock_fetch_prices.return_value = create_prices()

        observations = create_event_market_observations(
            MagicMock(),
            limit=2,
        )

        self.assertEqual(len(observations), 2)
        mock_fetch_prices.assert_called_once()
        mock_fetch_candidates.assert_called_once_with(
            unittest.mock.ANY,
            40,
        )


if __name__ == "__main__":
    unittest.main()
