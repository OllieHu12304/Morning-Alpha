"""將 TWSE 上市公司每日重大訊息轉成共同新聞格式。"""

from datetime import datetime
import hashlib
import json
import logging
from urllib.parse import urlencode

from http_client import fetch_text
from news_record import create_news_record


SOURCE = "twse_disclosure"
SOURCE_CATEGORY = "官方重大訊息"
SOURCE_NAME = "TWSE 上市公司每日重大訊息"
TWSE_DISCLOSURE_URL = (
    "https://openapi.twse.com.tw/v1/opendata/t187ap04_L"
)
MOPS_SEARCH_URL = "https://mops.twse.com.tw/mops/web/t05st01"
REQUEST_TIMEOUT = 20
REQUIRED_FIELDS = [
    "發言日期",
    "發言時間",
    "公司代號",
    "公司名稱",
    "主旨",
]

logger = logging.getLogger(__name__)


def clean_text(value):
    """將官方文字欄位轉成沒有前後空白的字串。"""
    if value is None:
        return ""

    return str(value).strip()


def normalize_fields(record):
    """清除欄位名稱空白，處理官方「主旨 」尾端空白。"""
    return {
        clean_text(field_name): clean_text(value)
        for field_name, value in record.items()
    }


def parse_publish_time(date_text, time_text):
    """將七碼民國日期與 HHMMSS 組成台北本地 datetime。"""
    normalized_date = clean_text(date_text)
    normalized_time = clean_text(time_text)

    if len(normalized_date) != 7 or not normalized_date.isdigit():
        raise ValueError(f"無效的 TWSE 發言日期：{date_text}")

    if len(normalized_time) > 6 or not normalized_time.isdigit():
        raise ValueError(f"無效的 TWSE 發言時間：{time_text}")

    normalized_time = normalized_time.zfill(6)
    year = int(normalized_date[:3]) + 1911

    try:
        return datetime(
            year,
            int(normalized_date[3:5]),
            int(normalized_date[5:7]),
            int(normalized_time[:2]),
            int(normalized_time[2:4]),
            int(normalized_time[4:6]),
        )
    except ValueError as error:
        raise ValueError(
            f"無效的 TWSE 發言日期或時間：{date_text} {time_text}"
        ) from error


def build_mops_url(ticker, publish_time, subject):
    """建立可去重且能開啟公司重大訊息查詢頁的官方 URL。"""
    identity = f"{ticker}|{publish_time.isoformat()}|{subject}"
    disclosure_id = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:16]
    query = urlencode({
        "TYPEK": "sii",
        "co_id": ticker,
        "firstin": "1",
        "inpuType": "co_id",
        "morning_alpha_id": disclosure_id,
        "off": "1",
        "spoke_date": publish_time.strftime("%Y%m%d"),
        "spoke_time": publish_time.strftime("%H%M%S"),
        "step": "1",
        "year": str(publish_time.year - 1911),
    })
    return f"{MOPS_SEARCH_URL}?{query}"


def fetch_disclosure_data():
    """下載 TWSE 每日重大訊息 JSON。"""
    headers = {
        "User-Agent": "MorningAlphaLearningProject/0.4",
        "Accept": "application/json",
    }
    return fetch_text(
        TWSE_DISCLOSURE_URL,
        source_name=SOURCE_NAME,
        timeout=REQUEST_TIMEOUT,
        headers=headers,
    )


def parse_disclosures(json_text):
    """解析官方 JSON，略過不完整資料並建立共同格式。"""
    try:
        raw_records = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError("TWSE 重大訊息不是有效 JSON。") from error

    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("TWSE 重大訊息最外層必須是非空 list。")

    articles = []
    skipped_count = 0

    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            skipped_count += 1
            continue

        fields = normalize_fields(raw_record)

        if any(not fields.get(field) for field in REQUIRED_FIELDS):
            skipped_count += 1
            continue

        try:
            publish_time = parse_publish_time(
                fields["發言日期"],
                fields["發言時間"],
            )
        except ValueError:
            skipped_count += 1
            continue

        ticker = fields["公司代號"]
        company_name = fields["公司名稱"]
        title = f"{ticker} {company_name}｜{fields['主旨']}"
        articles.append(create_news_record(
            source=SOURCE,
            source_category=SOURCE_CATEGORY,
            title=title,
            publish_time=publish_time,
            url=build_mops_url(
                ticker,
                publish_time,
                fields["主旨"],
            ),
        ))

    if skipped_count:
        logger.warning(
            "TWSE 重大訊息已略過 %s 筆不完整紀錄。",
            skipped_count,
        )

    if not articles:
        raise ValueError("TWSE 重大訊息沒有可用資料。")

    return articles


def fetch_articles():
    """下載並解析 TWSE 上市公司每日重大訊息。"""
    return parse_disclosures(fetch_disclosure_data())
