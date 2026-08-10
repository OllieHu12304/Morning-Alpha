"""依序執行 Morning Alpha 的完整資料更新流程。"""

import json
import sys

import pymysql
import requests

from analyze_keywords import (
    count_top_keywords,
    export_keyword_json,
    load_news_dataframe,
)
from analyze_news import create_dataframe, transform_dataframe
from export_news_json import (
    build_metadata,
    export_json,
    export_metadata,
    prepare_dashboard_records,
)
from generate_chart_data import (
    export_chart_data,
    generate_chart_data,
    load_news_records,
)
from logging_config import configure_logging
from news_sources import fetch_all_articles
from read_news import load_all_news
from store_news import save_news


def collect_and_store_news():
    """爬取、整理並將最新新聞寫入 MySQL。"""
    articles = fetch_all_articles()
    dataframe = create_dataframe(articles)
    dataframe = transform_dataframe(dataframe)
    return save_news(dataframe)


def export_dashboard_news():
    """從 MySQL 匯出 dashboard/news.json。"""
    dataframe = load_all_news()
    records = prepare_dashboard_records(dataframe)
    export_json(records)
    export_metadata(build_metadata())
    return len(records)


def build_chart_data():
    """從 news.json 產生 dashboard/chart_data.json。"""
    records = load_news_records()
    chart_data = generate_chart_data(records)
    export_chart_data(chart_data)
    return len(chart_data)


def build_keyword_data():
    """從 news.json 產生 dashboard/keyword.json。"""
    dataframe = load_news_dataframe()
    keyword_dataframe = count_top_keywords(dataframe)
    export_keyword_json(keyword_dataframe)
    return len(keyword_dataframe)


def run_pipeline():
    """依照相依順序執行所有資料更新步驟。"""
    print("Step 1/4：爬取、整理並儲存新聞…")
    inserted_news = collect_and_store_news()

    print("Step 2/4：匯出 Dashboard 新聞資料…")
    exported_news = export_dashboard_news()

    print("Step 3/4：產生 Dashboard 圖表資料…")
    chart_groups = build_chart_data()

    print("Step 4/4：產生 Top 20 關鍵字資料…")
    exported_keywords = build_keyword_data()

    return {
        "inserted_news": inserted_news,
        "exported_news": exported_news,
        "chart_groups": chart_groups,
        "exported_keywords": exported_keywords,
    }


def print_summary(summary):
    """顯示 pipeline 的執行結果。"""
    print("Morning Alpha 資料更新完成。")
    print(f"MySQL 新增新聞：{summary['inserted_news']} 筆")
    print(f"news.json 新聞：{summary['exported_news']} 筆")
    print(f"chart_data.json 統計群組：{summary['chart_groups']} 組")
    print(f"keyword.json 關鍵字：{summary['exported_keywords']} 個")


def main():
    """執行 pipeline，發生錯誤時停止並回傳失敗狀態。"""
    configure_logging()

    try:
        summary = run_pipeline()
        print_summary(summary)
        return 0
    except requests.RequestException as error:
        print(f"Pipeline 中止：下載新聞來源時發生錯誤：{error}")
    except pymysql.MySQLError as error:
        print(f"Pipeline 中止：MySQL 發生錯誤：{error}")
    except json.JSONDecodeError as error:
        print(f"Pipeline 中止：JSON 格式錯誤：{error}")
    except ValueError as error:
        print(f"Pipeline 中止：設定或資料錯誤：{error}")
    except OSError as error:
        print(f"Pipeline 中止：讀寫檔案時發生錯誤：{error}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
