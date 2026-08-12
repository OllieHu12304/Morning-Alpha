"""下載並解析 TWSE 上市個股每日盤後價格。"""

import json
import logging
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from http_client import fetch_text
from market_data_contract import (
    MARKET_PRICE_FIELD_MAP,
    MARKET_PRICE_SOURCE,
)


REQUEST_TIMEOUT = 20
EMPTY_NUMBER_VALUES = {"", "--", "---", "-"}
TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")
MARKET_DATA_READY_HOUR = 17
HISTORICAL_MARKET_URL = (
    "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
)
HISTORICAL_REQUIRED_FIELDS = {
    "證券代號",
    "證券名稱",
    "成交股數",
    "成交筆數",
    "成交金額",
    "開盤價",
    "最高價",
    "最低價",
    "收盤價",
    "漲跌價差",
}

logger = logging.getLogger(__name__)


def get_expected_trade_date(current_time=None):
    """估計此刻應可取得的最近平日；國定休市仍以官方資料為準。"""
    if current_time is None:
        current_time = datetime.now(TAIPEI_TIMEZONE)

    if current_time.tzinfo is None:
        raise ValueError("current_time 必須包含 timezone。")

    taipei_time = current_time.astimezone(TAIPEI_TIMEZONE)
    expected_date = taipei_time.date()

    if taipei_time.time() < time(hour=MARKET_DATA_READY_HOUR):
        expected_date -= timedelta(days=1)

    while expected_date.weekday() >= 5:
        expected_date -= timedelta(days=1)

    return expected_date


def assess_market_data_freshness(records, current_time=None):
    """回報官方資料日期，避免只看保存筆數誤以為行情已更新。"""
    if not records:
        raise ValueError("無法檢查空白的市場價格資料。")

    latest_trade_date = max(record["trade_date"] for record in records)
    expected_trade_date = get_expected_trade_date(current_time)
    return {
        "latest_trade_date": latest_trade_date.isoformat(),
        "expected_trade_date": expected_trade_date.isoformat(),
        "is_stale": latest_trade_date < expected_trade_date,
    }


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


def fetch_historical_market_price_data(trade_date):
    """下載指定日期的 TWSE 全部上市股票盤後行情。"""
    if not isinstance(trade_date, date):
        raise ValueError("trade_date 必須是 date。")

    date_text = trade_date.strftime("%Y%m%d")
    url = (
        f"{HISTORICAL_MARKET_URL}?date={date_text}"
        "&type=ALLBUT0999&response=json"
    )
    return fetch_text(
        url,
        source_name=f"TWSE {trade_date.isoformat()} 歷史盤後行情",
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": "MorningAlphaLearningProject/0.3",
            "Accept": "application/json",
        },
    )


def clean_text(value):
    """清除來源文字前後空白。"""
    if value is None:
        return ""

    return str(value).strip()


def clean_historical_text(value):
    """清除歷史行情欄位可能包含的 HTML 與空白。"""
    text = clean_text(value)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


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


def find_historical_stock_table(payload):
    """依欄位名稱尋找個股行情 table，不依賴易變的 table index。"""
    for table_record in payload.get("tables", []):
        fields = table_record.get("fields", [])

        if HISTORICAL_REQUIRED_FIELDS.issubset(set(fields)):
            return table_record

    raise ValueError("TWSE 歷史行情結構異常，找不到個股行情欄位。")


def create_historical_market_record(row, field_indexes, trade_date, fetched_at):
    """將 MI_INDEX 的一列資料轉成每日價格共同格式。"""
    def value(field_name):
        return clean_historical_text(row[field_indexes[field_name]])

    ticker = value("證券代號")
    name = value("證券名稱")

    if not ticker or not name:
        raise ValueError("TWSE 歷史行情缺少股票代號或名稱。")

    change_text = value("漲跌價差")
    sign_text = value("漲跌(+/-)") if "漲跌(+/-)" in field_indexes else ""

    if sign_text == "-" and change_text and not change_text.startswith("-"):
        change_text = f"-{change_text}"

    return {
        "ticker": ticker,
        "name": name,
        "exchange": MARKET_PRICE_SOURCE["exchange"],
        "trade_date": trade_date,
        "open_price": parse_decimal(value("開盤價"), "開盤價"),
        "high_price": parse_decimal(value("最高價"), "最高價"),
        "low_price": parse_decimal(value("最低價"), "最低價"),
        "close_price": parse_decimal(value("收盤價"), "收盤價"),
        "price_change": parse_decimal(change_text, "漲跌價差"),
        "volume": parse_integer(value("成交股數"), "成交股數"),
        "trade_value": parse_decimal(value("成交金額"), "成交金額"),
        "transaction_count": parse_integer(value("成交筆數"), "成交筆數"),
        "currency": MARKET_PRICE_SOURCE["currency"],
        "source": "TWSE 指定日期上市股票盤後行情",
        "fetched_at": fetched_at,
    }


def parse_historical_market_prices(json_text, trade_date, fetched_at=None):
    """解析指定日期 MI_INDEX；休市或無資料時回傳空 list。"""
    if not isinstance(trade_date, date):
        raise ValueError("trade_date 必須是 date。")

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError("TWSE 歷史行情不是有效 JSON。") from error

    if not isinstance(payload, dict):
        raise ValueError("TWSE 歷史行情最外層必須是 object。")

    if payload.get("stat") != "OK":
        return []

    table_record = find_historical_stock_table(payload)
    fields = table_record["fields"]
    rows = table_record.get("data", [])

    if not isinstance(rows, list) or not rows:
        return []

    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    if fetched_at.tzinfo is None:
        raise ValueError("fetched_at 必須包含 timezone。")

    field_indexes = {
        field_name: index
        for index, field_name in enumerate(fields)
    }
    records = []

    for row in rows:
        if not isinstance(row, list) or len(row) < len(fields):
            logger.warning("略過欄位數量不足的 TWSE 歷史行情紀錄。")
            continue

        try:
            records.append(create_historical_market_record(
                row,
                field_indexes,
                trade_date,
                fetched_at,
            ))
        except ValueError as error:
            logger.warning("略過無效 TWSE 歷史行情紀錄：%s", error)

    if not records:
        raise ValueError("TWSE 歷史行情沒有可使用的個股紀錄。")

    return records


def fetch_historical_market_prices(trade_date):
    """下載並解析一個指定日期的歷史盤後行情。"""
    return parse_historical_market_prices(
        fetch_historical_market_price_data(trade_date),
        trade_date,
    )


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
