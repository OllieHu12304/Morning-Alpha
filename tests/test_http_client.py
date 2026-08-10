"""測試新聞來源共用的 HTTP retry。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import http_client  # noqa: E402


class HttpClientTests(unittest.TestCase):
    def test_fetch_text_retries_then_returns_successful_response(self):
        response = Mock()
        response.text = "下載成功"
        response.raise_for_status.return_value = None

        with patch.object(
            http_client.requests,
            "get",
            side_effect=[requests.Timeout("逾時"), response],
        ) as request_get, patch.object(http_client.time, "sleep") as sleep:
            result = http_client.fetch_text(
                "https://example.com/feed",
                source_name="測試來源",
                timeout=10,
            )

        self.assertEqual(result, "下載成功")
        self.assertEqual(request_get.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_fetch_text_raises_after_maximum_attempts(self):
        with patch.object(
            http_client.requests,
            "get",
            side_effect=requests.ConnectionError("連線失敗"),
        ) as request_get, patch.object(http_client.time, "sleep") as sleep:
            with self.assertRaises(requests.ConnectionError):
                http_client.fetch_text(
                    "https://example.com/feed",
                    source_name="測試來源",
                    timeout=10,
                    max_attempts=3,
                )

        self.assertEqual(request_get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_fetch_text_rejects_invalid_attempt_count(self):
        with self.assertRaisesRegex(ValueError, "大於 0"):
            http_client.fetch_text(
                "https://example.com/feed",
                source_name="測試來源",
                timeout=10,
                max_attempts=0,
            )


if __name__ == "__main__":
    unittest.main()
