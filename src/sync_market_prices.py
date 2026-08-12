"""從 TWSE 官方 OpenAPI 更新每日盤後價格。"""

import sys

import pymysql
import requests

from logging_config import configure_logging
from market_price_store import save_market_prices
from twse_market_adapter import (
    assess_market_data_freshness,
    fetch_market_prices,
)


def run():
    """下載、驗證並保存 TWSE 每日價格。"""
    records = fetch_market_prices()
    result = save_market_prices(records)
    result.update(assess_market_data_freshness(records))
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
