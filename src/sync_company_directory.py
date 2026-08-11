"""從 TWSE 官方 OpenAPI 更新 Morning Alpha 公司資料。"""

import json
import sys

import pymysql
import requests

from company_directory import sync_company_records
from logging_config import configure_logging
from twse_company_adapter import fetch_companies


def run():
    """下載、驗證並保存 TWSE 上市公司資料。"""
    companies = fetch_companies()
    return sync_company_records(companies)


def main():
    """執行公司資料同步並提供安全的 terminal 訊息。"""
    configure_logging()

    try:
        imported_count = run()
        print(f"TWSE 公司資料同步完成：{imported_count} 筆。")
        return 0
    except requests.RequestException as error:
        print(f"公司資料同步失敗：下載錯誤：{error}")
    except pymysql.MySQLError as error:
        print(f"公司資料同步失敗：MySQL 錯誤：{error}")
    except (json.JSONDecodeError, ValueError) as error:
        print(f"公司資料同步失敗：資料錯誤：{error}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
