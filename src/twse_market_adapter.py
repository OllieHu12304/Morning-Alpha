"""下載並解析 TWSE 上市個股每日盤後價格。"""

import json
import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from http_client import fetch_text
from market_data_contract import (
    MARKET_PRICE_FIELD_MAP,
    MARKET_PRICE_SOURCE,
)


REQUEST_TIMEOUT = 20
EMPTY_NUMBER_VALUES = {"", "--", "---", "-"}

logger = logging.getLogger(__name__)


def fetch_market_price_data():
    """下載 TWSE 上市個股日成交資訊 JSON。"""
    headers = {
        "User-Agent": "MorningAlphaLearningProject/0.3",
        "Accept": "application/json",
    }
    return fetch_text(
        MARKET_PRICE_SOURCE["url"],
        source_name=MARKET_PRICE_SOURCE["name"],
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

    year = int(text[:3]) + 1911
    month = int(text[3:5])
    day = int(text[5:7])

    try:
        return date(year, month, day)
    except ValueError as error:
        raise ValueError(f"無效的 TWSE 民國日期：{text}") from error


def parse_decimal(value, field_name):
    """將含千分位的官方數字轉成 Decimal，空值轉成 None。"""
    text = clean_text(value).replace(",", "")

    if text in EMPTY_NUMBER_VALUES:
        return None

    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"{field_name} 不是有效數字：{value}") from error


def parse_integer(value, field_name):
    """解析必須是整數的成交量與成交筆數。"""
    number = parse_decimal(value, field_name)

    if number is None:
        return None

    if number != number.to_integral_value() or number < 0:
        raise ValueError(f"{field_name} 必須是非負整數：{value}")

    return int(number)


def validate_raw_schema(raw_records):
    """偵測 TWSE 是否已移除或改名必要欄位。"""
    expected_fields = set(MARKET_PRICE_FIELD_MAP)
    object_records = [
        record
        for record in raw_records
        if isinstance(record, dict)
    ]

    if not object_records:
        raise ValueError("TWSE 價格資料沒有 object 紀錄。")

    if not expected_fields.issubset(object_records[0]):
        missing_fields = sorted(expected_fields - set(object_records[0]))
        raise ValueError(
            "TWSE 價格資料結構異常，缺少欄位："
            + ", ".join(missing_fields)
        )


def create_market_price_record(raw_record, fetched_at):
    """將一筆 TWSE 紀錄轉成 Morning Alpha 共同格式。"""
    ticker = clean_text(raw_record.get("Code"))
    name = clean_text(raw_record.get("Name"))

    if not ticker or not name:
        raise ValueError("TWSE 價格紀錄缺少股票代號或名稱。")

    return {
        "ticker": ticker,
        "name": name,
        "exchange": MARKET_PRICE_SOURCE["exchange"],
        "trade_date": parse_roc_date(raw_record.get("Date")),
        "open_price": parse_decimal(
            raw_record.get("OpeningPrice"),
            "OpeningPrice",
        ),
        "high_price": parse_decimal(
            raw_record.get("HighestPrice"),
            "HighestPrice",
        ),
        "low_price": parse_decimal(
            raw_record.get("LowestPrice"),
            "LowestPrice",
        ),
        "close_price": parse_decimal(
            raw_record.get("ClosingPrice"),
            "ClosingPrice",
        ),
        "price_change": parse_decimal(
            raw_record.get("Change"),
            "Change",
        ),
        "volume": parse_integer(raw_record.get("TradeVolume"), "TradeVolume"),
        "trade_value": parse_decimal(
            raw_record.get("TradeValue"),
            "TradeValue",
        ),
        "transaction_count": parse_integer(
            raw_record.get("Transaction"),
            "Transaction",
        ),
        "currency": MARKET_PRICE_SOURCE["currency"],
        "source": MARKET_PRICE_SOURCE["name"],
        "fetched_at": fetched_at,
    }


def parse_market_prices(json_text, fetched_at=None):
    """將 TWSE JSON 轉成每日價格共同格式。"""
    try:
        raw_records = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError("TWSE 價格資料不是有效 JSON。") from error

    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("TWSE 價格資料最外層必須是非空 list。")

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
            records.append(create_market_price_record(raw_record, fetched_at))
        except ValueError as error:
            skipped_count += 1
            logger.warning("略過無效 TWSE 價格紀錄：%s", error)

    if skipped_count:
        logger.warning("TWSE 價格資料已略過 %s 筆無效紀錄。", skipped_count)

    if not records:
        raise ValueError("TWSE 價格資料沒有可使用的紀錄。")

    return records


def fetch_market_prices():
    """下載並解析 TWSE 上市個股每日價格。"""
    return parse_market_prices(fetch_market_price_data())
