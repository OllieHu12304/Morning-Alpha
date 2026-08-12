"""從 TWSE 官方 OpenAPI 更新每日盤後價格。"""

import sys
from datetime import timedelta

import pymysql
import requests

from logging_config import configure_logging
from market_price_store import load_market_date_state, save_market_prices
from twse_market_adapter import (
    assess_market_data_freshness,
    fetch_historical_market_prices,
    fetch_market_prices,
    get_expected_trade_date,
)


INITIAL_BACKFILL_CALENDAR_DAYS = 14


def get_missing_market_dates(summary, stored_dates, expected_date):
    """初次回補兩週；後續只處理最新保存日期之後的缺漏平日。"""
    earliest_backfill_date = expected_date - timedelta(
        days=INITIAL_BACKFILL_CALENDAR_DAYS - 1
    )

    if summary["date_count"] <= 1 or summary["maximum_date"] is None:
        start_date = earliest_backfill_date
    else:
        start_date = max(
            summary["maximum_date"] + timedelta(days=1),
            earliest_backfill_date,
        )

    missing_dates = []
    current_date = start_date

    while current_date <= expected_date:
        if current_date.weekday() < 5 and current_date not in stored_dates:
            missing_dates.append(current_date)

        current_date += timedelta(days=1)

    return missing_dates


def fetch_missing_market_prices(expected_date):
    """只下載 Database 缺少的候選交易日，休市日安全略過。"""
    range_start = expected_date - timedelta(
        days=INITIAL_BACKFILL_CALENDAR_DAYS - 1
    )
    summary, stored_dates = load_market_date_state(
        range_start,
        expected_date,
    )
    missing_dates = get_missing_market_dates(
        summary,
        stored_dates,
        expected_date,
    )
    records = []
    completed_dates = []

    for missing_date in missing_dates:
        date_records = fetch_historical_market_prices(missing_date)

        if date_records:
            records.extend(date_records)
            completed_dates.append(missing_date.isoformat())

    return records, completed_dates


def run():
    """下載、驗證並保存 TWSE 每日價格。"""
    records = fetch_market_prices()
    result = save_market_prices(records)
    expected_date = get_expected_trade_date()
    historical_records, backfilled_dates = fetch_missing_market_prices(
        expected_date
    )

    if historical_records:
        historical_result = save_market_prices(historical_records)
        result["source_count"] += historical_result["source_count"]
        result["saved_count"] += historical_result["saved_count"]
        result["skipped_count"] += historical_result["skipped_count"]

    all_records = records + historical_records
    result.update(assess_market_data_freshness(all_records))
    result["backfilled_trade_dates"] = backfilled_dates
    return result


def main():
    """執行價格同步並顯示安全摘要。"""
    configure_logging()

    try:
        result = run()
        print(
            "TWSE 每日價格同步完成："
            f"來源 {result['source_count']} 筆，"
            f"保存 {result['saved_count']} 筆，"
            f"略過 {result['skipped_count']} 筆未對應證券。"
        )
        print(
            f"TWSE 最新交易日：{result['latest_trade_date']}；"
            f"預期最近交易日：{result['expected_trade_date']}。"
        )

        if result["is_stale"]:
            print("警告：TWSE 回傳的盤後資料尚未更新到預期交易日。")

        if result["backfilled_trade_dates"]:
            print(
                "歷史價格回補："
                + "、".join(result["backfilled_trade_dates"])
            )
        return 0
    except requests.RequestException as error:
        print(f"每日價格同步失敗：下載錯誤：{error}")
    except pymysql.MySQLError as error:
        print(f"每日價格同步失敗：MySQL 錯誤：{error}")
    except (KeyError, ValueError) as error:
        print(f"每日價格同步失敗：資料錯誤：{error}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
