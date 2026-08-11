"""下載並解析 TWSE 上市公司季度財務摘要。"""

import json
import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from http_client import fetch_text
from market_data_contract import FINANCIAL_FIELD_MAP, FINANCIAL_SOURCE


REQUEST_TIMEOUT = 20
EMPTY_NUMBER_VALUES = {"", "--", "---", "-"}

logger = logging.getLogger(__name__)


def fetch_financial_data():
    """下載 TWSE 上市公司各產業 EPS 統計資訊。"""
    headers = {
        "User-Agent": "MorningAlphaLearningProject/0.3",
        "Accept": "application/json",
    }
    return fetch_text(
        FINANCIAL_SOURCE["url"],
        source_name=FINANCIAL_SOURCE["name"],
        timeout=REQUEST_TIMEOUT,
        headers=headers,
    )


def clean_text(value):
    """清除來源文字前後空白。"""
    if value is None:
        return ""

    return str(value).strip()


def parse_roc_date(value):
    """將民國七碼年月日轉成 Python date。"""
    text = clean_text(value)

    if len(text) != 7 or not text.isdigit():
        raise ValueError(f"無效的 TWSE 民國日期：{text}")

    try:
        return date(
            int(text[:3]) + 1911,
            int(text[3:5]),
            int(text[5:7]),
        )
    except ValueError as error:
        raise ValueError(f"無效的 TWSE 民國日期：{text}") from error


def parse_fiscal_year(value):
    """將民國會計年度轉成西元年度。"""
    text = clean_text(value)

    if not text.isdigit():
        raise ValueError(f"無效的 TWSE 會計年度：{text}")

    year = int(text) + 1911

    if year < 1900 or year > 2200:
        raise ValueError(f"無效的 TWSE 會計年度：{text}")

    return year


def parse_fiscal_quarter(value):
    """將季別轉成 1 到 4 的整數。"""
    text = clean_text(value)

    if not text.isdigit() or int(text) not in [1, 2, 3, 4]:
        raise ValueError(f"無效的 TWSE 季別：{text}")

    return int(text)


def parse_decimal(value, field_name):
    """將官方財務數值原尺度轉成 Decimal，空值轉成 None。"""
    text = clean_text(value).replace(",", "")

    if text in EMPTY_NUMBER_VALUES:
        return None

    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"{field_name} 不是有效數字：{value}") from error


def validate_raw_schema(raw_records):
    """偵測 TWSE 財務資料必要欄位是否改名或消失。"""
    expected_fields = set(FINANCIAL_FIELD_MAP)
    object_records = [
        record
        for record in raw_records
        if isinstance(record, dict)
    ]

    if not object_records:
        raise ValueError("TWSE 財務資料沒有 object 紀錄。")

    if not expected_fields.issubset(object_records[0]):
        missing_fields = sorted(expected_fields - set(object_records[0]))
        raise ValueError(
            "TWSE 財務資料結構異常，缺少欄位："
            + ", ".join(missing_fields)
        )


def create_financial_record(raw_record, fetched_at):
    """將一筆 TWSE 財務紀錄轉成共同格式。"""
    ticker = clean_text(raw_record.get("公司代號"))
    name = clean_text(raw_record.get("公司名稱"))

    if not ticker or not name:
        raise ValueError("TWSE 財務紀錄缺少公司代號或名稱。")

    return {
        "ticker": ticker,
        "name": name,
        "exchange": FINANCIAL_SOURCE["exchange"],
        "report_date": parse_roc_date(raw_record.get("出表日期")),
        "fiscal_year": parse_fiscal_year(raw_record.get("年度")),
        "fiscal_quarter": parse_fiscal_quarter(raw_record.get("季別")),
        "industry": clean_text(raw_record.get("產業別")) or None,
        "earnings_per_share": parse_decimal(
            raw_record.get("基本每股盈餘(元)"),
            "基本每股盈餘(元)",
        ),
        "face_value_text": clean_text(
            raw_record.get("普通股每股面額")
        ) or None,
        "operating_revenue": parse_decimal(
            raw_record.get("營業收入"),
            "營業收入",
        ),
        "operating_income": parse_decimal(
            raw_record.get("營業利益"),
            "營業利益",
        ),
        "non_operating_income_expense": parse_decimal(
            raw_record.get("營業外收入及支出"),
            "營業外收入及支出",
        ),
        "net_income": parse_decimal(
            raw_record.get("稅後淨利"),
            "稅後淨利",
        ),
        "currency": FINANCIAL_SOURCE["currency"],
        "source": FINANCIAL_SOURCE["name"],
        "fetched_at": fetched_at,
    }


def parse_financial_records(json_text, fetched_at=None):
    """將 TWSE JSON 轉成季度財務共同格式。"""
    try:
        raw_records = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError("TWSE 財務資料不是有效 JSON。") from error

    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("TWSE 財務資料最外層必須是非空 list。")

    validate_raw_schema(raw_records)

    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    if fetched_at.tzinfo is None:
        raise ValueError("fetched_at 必須包含 timezone。")

    records = []
    skipped_count = 0

    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            skipped_count += 1
            continue

        try:
            records.append(create_financial_record(raw_record, fetched_at))
        except ValueError as error:
            skipped_count += 1
            logger.warning("略過無效 TWSE 財務紀錄：%s", error)

    if skipped_count:
        logger.warning("TWSE 財務資料已略過 %s 筆無效紀錄。", skipped_count)

    if not records:
        raise ValueError("TWSE 財務資料沒有可使用的紀錄。")

    return records


def fetch_financial_records():
    """下載並解析 TWSE 上市公司季度財務摘要。"""
    return parse_financial_records(fetch_financial_data())
