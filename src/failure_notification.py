"""透過可選的 Discord Webhook 傳送 Pipeline 失敗通知。"""

import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from store_news import load_environment


WEBHOOK_ENVIRONMENT_NAME = "PIPELINE_FAILURE_WEBHOOK_URL"
WEBHOOK_TIMEOUT_SECONDS = 10
MAX_DISCORD_CONTENT_LENGTH = 2000


def get_webhook_url():
    """讀取可選的 Discord Webhook URL。"""
    load_environment()
    return os.getenv(WEBHOOK_ENVIRONMENT_NAME, "").strip()


def validate_discord_webhook_url(webhook_url):
    """只接受 Discord HTTPS webhook，避免誤傳到其他主機。"""
    parsed_url = urlparse(webhook_url)
    hostname = (parsed_url.hostname or "").lower()
    is_discord_host = (
        hostname == "discord.com"
        or hostname.endswith(".discord.com")
    )
    path_parts = [part for part in parsed_url.path.split("/") if part]

    if (
        parsed_url.scheme != "https"
        or not is_discord_host
        or not parsed_url.path.startswith("/api/webhooks/")
        or len(path_parts) < 4
    ):
        raise ValueError(
            "PIPELINE_FAILURE_WEBHOOK_URL 必須是 Discord HTTPS webhook URL。"
        )


def build_failure_message(error_message, occurred_at=None):
    """建立不超過 Discord content 上限的純文字通知。"""
    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc)

    occurred_text = occurred_at.astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    content = (
        "Morning Alpha Pipeline 執行失敗\n"
        f"時間：{occurred_text}\n"
        f"原因：{error_message}\n"
        "請查看 data/processed/morning_alpha.log。"
    )
    return content[:MAX_DISCORD_CONTENT_LENGTH]


def send_failure_notification(error_message):
    """有設定 Webhook 時送出一次通知，未設定則直接跳過。"""
    webhook_url = get_webhook_url()

    if not webhook_url:
        return False

    validate_discord_webhook_url(webhook_url)
    response = requests.post(
        webhook_url,
        json={
            "content": build_failure_message(error_message),
            "allowed_mentions": {"parse": []},
        },
        timeout=WEBHOOK_TIMEOUT_SECONDS,
        allow_redirects=False,
    )

    if 300 <= response.status_code < 400:
        raise requests.HTTPError("Discord Webhook 不接受 redirect。")

    response.raise_for_status()
    return True
