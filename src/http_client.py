"""提供新聞來源共用的簡單 HTTP retry。"""

import logging
import time

import requests


DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1

logger = logging.getLogger(__name__)


def fetch_text(
    url,
    source_name,
    timeout,
    headers=None,
    max_attempts=DEFAULT_MAX_ATTEMPTS,
    retry_delay=DEFAULT_RETRY_DELAY,
):
    """下載文字；暫時失敗時最多嘗試 max_attempts 次。"""
    if max_attempts < 1:
        raise ValueError("max_attempts 必須大於 0。")

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                "%s 下載嘗試 %s/%s：%s",
                source_name,
                attempt,
                max_attempts,
                url,
            )
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info("%s 下載成功。", source_name)
            return response.text
        except requests.RequestException as error:
            if attempt == max_attempts:
                logger.error(
                    "%s 下載失敗，已達最大嘗試次數：%s",
                    source_name,
                    error,
                )
                raise

            logger.warning(
                "%s 下載失敗，%s 秒後重試：%s",
                source_name,
                retry_delay,
                error,
            )
            time.sleep(retry_delay)

    raise RuntimeError("HTTP retry 流程發生未預期錯誤。")
