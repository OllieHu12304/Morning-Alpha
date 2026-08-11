"""從 TWSE 官方 OpenAPI 更新季度財務摘要。"""

import sys

import pymysql
import requests

from financial_metric_store import save_financial_metrics
from logging_config import configure_logging
from twse_financial_adapter import fetch_financial_records


def run():
    """下載、驗證並保存 TWSE 財務摘要。"""
    records = fetch_financial_records()
    return save_financial_metrics(records)


def main():
    """執行財務同步並顯示安全摘要。"""
    configure_logging()

    try:
        result = run()
        print(
            "TWSE 財務資料同步完成："
            f"來源 {result['source_count']} 筆，"
            f"保存 {result['saved_count']} 筆，"
            f"略過 {result['skipped_count']} 筆未對應證券。"
        )
        return 0
    except requests.RequestException as error:
        print(f"財務資料同步失敗：下載錯誤：{error}")
    except pymysql.MySQLError as error:
        print(f"財務資料同步失敗：MySQL 錯誤：{error}")
    except (KeyError, ValueError) as error:
        print(f"財務資料同步失敗：資料錯誤：{error}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
