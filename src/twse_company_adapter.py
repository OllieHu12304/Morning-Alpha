"""下載並解析臺灣證券交易所上市公司基本資料。"""

import json
import logging

from http_client import fetch_text


TWSE_COMPANY_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
REQUEST_TIMEOUT = 20
SOURCE_NAME = "TWSE 上市公司基本資料"
REQUIRED_FIELDS = ["公司代號", "公司名稱", "公司簡稱", "產業別"]

logger = logging.getLogger(__name__)


def fetch_company_data():
    """下載 TWSE 上市公司基本資料 JSON。"""
    headers = {
        "User-Agent": "MorningAlphaLearningProject/0.3",
        "Accept": "application/json",
    }
    return fetch_text(
        TWSE_COMPANY_URL,
        source_name=SOURCE_NAME,
        timeout=REQUEST_TIMEOUT,
        headers=headers,
    )


def clean_text(value):
    """將官方文字欄位去除前後空白。"""
    if value is None:
        return ""

    return str(value).strip()


def parse_companies(json_text):
    """將 TWSE JSON 轉成 Morning Alpha 公司共同格式。"""
    try:
        raw_records = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError("TWSE 公司資料不是有效 JSON。") from error

    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("TWSE 公司資料最外層必須是非空 list。")

    companies = []
    skipped_count = 0

    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            skipped_count += 1
            continue

        fields = {
            field: clean_text(raw_record.get(field))
            for field in REQUIRED_FIELDS
        }

        if any(not fields[field] for field in REQUIRED_FIELDS):
            skipped_count += 1
            continue

        aliases = []

        for alias in [fields["公司簡稱"], fields["公司名稱"]]:
            if alias not in aliases:
                aliases.append(alias)

        companies.append({
            "name": fields["公司名稱"],
            "short_name": fields["公司簡稱"],
            "industry": fields["產業別"],
            "market": "TWSE",
            "ticker": fields["公司代號"],
            "exchange": "TWSE",
            "currency": "TWD",
            "aliases": aliases,
        })

    if skipped_count:
        logger.warning("TWSE 公司資料已略過 %s 筆不完整紀錄。", skipped_count)

    if not companies:
        raise ValueError("TWSE 公司資料沒有可使用的公司紀錄。")

    return companies


def fetch_companies():
    """下載並解析 TWSE 上市公司基本資料。"""
    return parse_companies(fetch_company_data())
