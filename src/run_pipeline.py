"""依序執行 Morning Alpha 的完整資料更新流程。"""

import json
import logging
import sys
import time

import pymysql
import requests

from analyze_keywords import (
    count_top_keywords,
    export_keyword_json,
    load_news_dataframe,
)
from analyze_news import create_dataframe, transform_dataframe
from daily_brief import build_daily_brief
from daily_brief_store import save_daily_brief
from daily_brief_window import get_latest_brief_date
from export_news_json import (
    build_metadata,
    export_json,
    export_metadata,
    prepare_dashboard_records,
)
from event_grouping import group_similar_events
from generate_chart_data import (
    export_chart_data,
    generate_chart_data,
    load_news_records,
)
from failure_notification import send_failure_notification
from history_retention import cleanup_history
from logging_config import configure_logging
from news_sources import fetch_all_articles_with_status
from news_company_links import run_news_company_sync
from pipeline_history import (
    create_pending_step_results,
    save_pipeline_run,
    utc_now,
    update_step_result,
)
from read_news import get_balanced_recent_news, load_all_news
from source_health import save_source_health_events
from store_news import save_news
from sync_company_directory import run as sync_company_directory
from sync_financial_metrics import run as sync_financial_metrics
from sync_market_prices import run as sync_market_prices
from watchlist import ensure_watchlist_table


logger = logging.getLogger(__name__)


def collect_and_store_news():
    """爬取、整理並將最新新聞寫入 MySQL。"""
    articles, source_results = (
        fetch_all_articles_with_status()
    )
    save_source_health_events(source_results)

    successful_sources = [
        result["source_name"]
        for result in source_results
        if result["status"] == "success"
    ]
    failed_sources = [
        result["source_name"]
        for result in source_results
        if result["status"] == "failure"
    ]

    if not successful_sources:
        failed_labels = "、".join(failed_sources)
        raise ValueError(f"所有新聞來源都失敗：{failed_labels}。")

    dataframe = create_dataframe(articles)
    dataframe = transform_dataframe(dataframe)
    inserted_news = save_news(dataframe)
    return inserted_news, successful_sources, failed_sources


def export_dashboard_news():
    """從 MySQL 匯出 dashboard/news.json。"""
    dataframe = load_all_news()
    dataframe = get_balanced_recent_news(dataframe)
    records = prepare_dashboard_records(dataframe)
    records = group_similar_events(records)
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


def generate_and_store_daily_brief():
    """從 MySQL 新聞建立最近一個完整時間窗的每日晨報。"""
    dataframe = load_all_news()
    records = prepare_dashboard_records(dataframe)
    brief_date = get_latest_brief_date()
    brief = build_daily_brief(records, brief_date)
    save_daily_brief(brief)
    return {
        "brief_date": brief["brief_date"],
        "article_count": brief["article_count"],
    }


def sync_company_data():
    """同步公司目錄，並確保相依的本機追蹤清單 table 存在。"""
    imported_count = sync_company_directory()
    ensure_watchlist_table()
    return imported_count


def get_duration_ms(start_time):
    """將 perf_counter 經過時間轉成非負毫秒。"""
    duration_ms = round((time.perf_counter() - start_time) * 1000)
    return max(0, duration_ms)


def execute_pipeline_step(step_results, step, function):
    """執行單一步驟，失敗時先記錄步驟狀態再重新拋出錯誤。"""
    step_start_time = time.perf_counter()

    try:
        result = function()
    except Exception:
        update_step_result(
            step_results,
            step,
            "failure",
            get_duration_ms(step_start_time),
        )
        raise

    return result, get_duration_ms(step_start_time)


def save_failed_run_without_hiding_error(run_result):
    """盡力保存失敗紀錄，但不以 history 錯誤覆蓋原始錯誤。"""
    try:
        save_pipeline_run(run_result)
    except (pymysql.MySQLError, OSError, TypeError, ValueError) as error:
        logger.error("無法保存 Pipeline 失敗紀錄：%s", error)


def cleanup_history_without_hiding_result():
    """盡力清理 history，但不改變 Pipeline 原本執行結果。"""
    try:
        deleted_counts = cleanup_history()
    except (pymysql.MySQLError, OSError, ValueError) as error:
        logger.error("無法清理過期歷史紀錄：%s", error)
        return None

    logger.info(
        "歷史紀錄清理完成：source_health_events %s 筆，pipeline_runs %s 筆。",
        deleted_counts["source_health_events"],
        deleted_counts["pipeline_runs"],
    )
    return deleted_counts


def send_failure_notification_without_hiding_error(error_message):
    """盡力通知 Pipeline 失敗，但不改變原本 exit code。"""
    try:
        return send_failure_notification(error_message)
    except (requests.RequestException, OSError, ValueError) as error:
        logger.error(
            "無法傳送 Pipeline 失敗通知：%s",
            type(error).__name__,
        )
        return False


def get_history_error_message(error):
    """產生適合由 Dashboard 顯示且不含內部設定的錯誤。"""
    if isinstance(error, requests.RequestException):
        return f"下載外部資料失敗：{error}"

    if isinstance(error, pymysql.MySQLError):
        return "MySQL 操作失敗，請查看 Pipeline log。"

    if isinstance(error, json.JSONDecodeError):
        return f"JSON 格式錯誤：{error}"

    if isinstance(error, ValueError):
        return str(error)

    if isinstance(error, OSError):
        return "檔案讀寫失敗，請查看 Pipeline log。"

    return "未預期的 Pipeline 錯誤，請查看 Pipeline log。"


def get_terminal_error_message(error):
    """建立原有 terminal 風格的 Pipeline 錯誤訊息。"""
    if isinstance(error, requests.RequestException):
        return f"Pipeline 中止：下載外部資料時發生錯誤：{error}"

    if isinstance(error, pymysql.MySQLError):
        return f"Pipeline 中止：MySQL 發生錯誤：{error}"

    if isinstance(error, json.JSONDecodeError):
        return f"Pipeline 中止：JSON 格式錯誤：{error}"

    if isinstance(error, ValueError):
        return f"Pipeline 中止：設定或資料錯誤：{error}"

    if isinstance(error, OSError):
        return f"Pipeline 中止：讀寫檔案時發生錯誤：{error}"

    return "Pipeline 中止：未預期錯誤，請查看 log。"


def run_pipeline():
    """依照相依順序執行所有資料更新步驟。"""
    started_at = utc_now()
    pipeline_start_time = time.perf_counter()
    step_results = create_pending_step_results()
    current_step = "collect_news"

    try:
        print("Step 1/9：爬取、整理並儲存新聞…")
        collect_result, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            collect_and_store_news,
        )
        inserted_news, successful_sources, failed_sources = collect_result
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            {
                "inserted_news": inserted_news,
                "successful_sources": successful_sources,
                "failed_sources": failed_sources,
            },
        )

        current_step = "sync_companies"
        print("Step 2/9：同步 TWSE 公司資料…")
        imported_companies, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            sync_company_data,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            {"imported_companies": imported_companies},
        )

        current_step = "link_news_companies"
        print("Step 3/9：建立新聞公司關聯…")
        company_link_result, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            run_news_company_sync,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            company_link_result,
        )

        current_step = "sync_market_prices"
        print("Step 4/9：同步 TWSE 每日價格…")
        market_price_result, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            sync_market_prices,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            market_price_result,
        )

        current_step = "sync_financial_metrics"
        print("Step 5/9：同步 TWSE 財務摘要…")
        financial_metric_result, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            sync_financial_metrics,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            financial_metric_result,
        )

        current_step = "daily_brief"
        print("Step 6/9：產生並保存每日晨報…")
        daily_brief_result, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            generate_and_store_daily_brief,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            daily_brief_result,
        )

        current_step = "export_news"
        print("Step 7/9：匯出 Dashboard 新聞資料…")
        exported_news, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            export_dashboard_news,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            {"exported_news": exported_news},
        )

        current_step = "chart_data"
        print("Step 8/9：產生 Dashboard 圖表資料…")
        chart_groups, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            build_chart_data,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            {"chart_groups": chart_groups},
        )

        current_step = "keywords"
        print("Step 9/9：產生 Top 20 關鍵字資料…")
        exported_keywords, step_duration = execute_pipeline_step(
            step_results,
            current_step,
            build_keyword_data,
        )
        update_step_result(
            step_results,
            current_step,
            "success",
            step_duration,
            {"exported_keywords": exported_keywords},
        )
    except Exception as error:
        save_failed_run_without_hiding_error({
            "status": "failure",
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_ms": get_duration_ms(pipeline_start_time),
            "failed_step": current_step,
            "step_results": step_results,
            "error_message": get_history_error_message(error),
        })
        cleanup_history_without_hiding_result()
        raise

    summary = {
        "inserted_news": inserted_news,
        "exported_news": exported_news,
        "chart_groups": chart_groups,
        "exported_keywords": exported_keywords,
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
        "imported_companies": imported_companies,
        "company_links": company_link_result["link_count"],
        "market_prices": market_price_result["saved_count"],
        "market_latest_trade_date": market_price_result.get(
            "latest_trade_date"
        ),
        "market_expected_trade_date": market_price_result.get(
            "expected_trade_date"
        ),
        "market_data_is_stale": market_price_result.get("is_stale", False),
        "financial_metrics": financial_metric_result["saved_count"],
        "daily_brief_date": daily_brief_result["brief_date"],
        "daily_brief_articles": daily_brief_result["article_count"],
    }
    save_pipeline_run({
        "status": "success",
        "started_at": started_at,
        "finished_at": utc_now(),
        "duration_ms": get_duration_ms(pipeline_start_time),
        "failed_step": None,
        "step_results": step_results,
        "error_message": None,
    })
    cleanup_history_without_hiding_result()
    return summary


def print_summary(summary):
    """顯示 pipeline 的執行結果。"""
    print("Morning Alpha 資料更新完成。")
    print(f"MySQL 新增新聞：{summary['inserted_news']} 筆")
    print(f"TWSE 公司資料：{summary['imported_companies']} 筆")
    print(f"新聞公司關聯：{summary['company_links']} 筆")
    print(f"每日價格保存：{summary['market_prices']} 筆")
    if summary.get("market_latest_trade_date"):
        print(
            f"TWSE 最新交易日：{summary['market_latest_trade_date']}；"
            f"預期最近交易日：{summary['market_expected_trade_date']}"
        )

    if summary.get("market_data_is_stale"):
        print("市場資料警告：TWSE 盤後資料尚未更新到預期交易日。")
    print(f"財務摘要保存：{summary['financial_metrics']} 筆")
    print(
        f"每日晨報：{summary['daily_brief_date']}，"
        f"收錄 {summary['daily_brief_articles']} 篇"
    )
    print(f"news.json 新聞：{summary['exported_news']} 筆")
    print(f"chart_data.json 統計群組：{summary['chart_groups']} 組")
    print(f"keyword.json 關鍵字：{summary['exported_keywords']} 個")
    print(f"成功來源：{'、'.join(summary['successful_sources'])}")

    if summary["failed_sources"]:
        print(f"失敗來源：{'、'.join(summary['failed_sources'])}")
    else:
        print("失敗來源：無")


def main():
    """執行 pipeline，發生錯誤時停止並回傳失敗狀態。"""
    configure_logging()

    try:
        summary = run_pipeline()
        print_summary(summary)
        return 0
    except (
        requests.RequestException,
        pymysql.MySQLError,
        json.JSONDecodeError,
        ValueError,
        OSError,
    ) as error:
        print(get_terminal_error_message(error))
        send_failure_notification_without_hiding_error(
            get_history_error_message(error)
        )
    except Exception as error:
        logger.exception("Pipeline 發生未預期錯誤。")
        print(get_terminal_error_message(error))
        send_failure_notification_without_hiding_error(
            get_history_error_message(error)
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
