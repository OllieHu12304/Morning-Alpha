"""測試可選的 Discord Pipeline 失敗通知。"""

import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import failure_notification  # noqa: E402


class FailureNotificationTests(unittest.TestCase):
    @patch("failure_notification.load_environment")
    @patch("failure_notification.requests.post")
    def test_missing_webhook_skips_network_request(
        self,
        post_request,
        mock_load_environment,
    ):
        with patch.dict(os.environ, {}, clear=True):
            sent = failure_notification.send_failure_notification("測試錯誤")

        self.assertFalse(sent)
        post_request.assert_not_called()
        mock_load_environment.assert_called_once_with()

    def test_invalid_webhook_host_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Discord HTTPS"):
            failure_notification.validate_discord_webhook_url(
                "https://example.com/api/webhooks/123/token"
            )

    @patch("failure_notification.load_environment")
    @patch("failure_notification.requests.post")
    def test_send_uses_content_and_disables_mentions(
        self,
        post_request,
        mock_load_environment,
    ):
        response = MagicMock()
        response.status_code = 204
        post_request.return_value = response
        webhook_url = "https://discord.com/api/webhooks/123/test-token"

        with patch.dict(
            os.environ,
            {"PIPELINE_FAILURE_WEBHOOK_URL": webhook_url},
            clear=True,
        ):
            sent = failure_notification.send_failure_notification(
                "所有新聞來源都失敗"
            )

        self.assertTrue(sent)
        payload = post_request.call_args.kwargs["json"]
        self.assertIn("Morning Alpha Pipeline 執行失敗", payload["content"])
        self.assertIn("所有新聞來源都失敗", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        self.assertEqual(
            post_request.call_args.kwargs["timeout"],
            10,
        )
        self.assertFalse(post_request.call_args.kwargs["allow_redirects"])
        response.raise_for_status.assert_called_once_with()
        mock_load_environment.assert_called_once_with()

    def test_failure_message_has_discord_length_limit(self):
        occurred_at = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
        message = failure_notification.build_failure_message(
            "錯" * 3000,
            occurred_at=occurred_at,
        )

        self.assertLessEqual(len(message), 2000)


if __name__ == "__main__":
    unittest.main()
