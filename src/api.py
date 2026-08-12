"""提供 Morning Alpha Dashboard 使用的 MySQL API。"""

import json
from pathlib import Path

import pandas as pd
import pymysql
from flask import Flask, jsonify, request

from analyze_keywords import count_top_keywords, create_title_dataframe
from company_market_data import (
    load_company_financial_metrics,
    load_company_market_prices,
    load_market_companies,
)
from daily_brief_store import load_daily_briefs
from event_grouping import group_similar_events
from event_market_analysis import (
    ANALYSIS_TYPE,
    LIMITATIONS as EVENT_MARKET_LIMITATIONS,
    METHODOLOGY as EVENT_MARKET_METHODOLOGY,
    load_event_market_analysis,
)
from export_news_json import prepare_dashboard_records
from generate_chart_data import generate_chart_data
from news_company_links import load_news_company_links
from pipeline_history import build_pipeline_run_records, load_pipeline_runs
from pipeline_process import get_pipeline_status, start_pipeline
from personalized_brief import load_personalized_brief
from read_news import get_balanced_recent_news, load_all_news
from source_health import build_source_health_summary, load_source_health_events
from watchlist import (
    add_watchlist_company,
    load_watchlist,
    remove_watchlist_company,
)


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"
DASHBOARD_REQUEST_HEADER = "X-Morning-Alpha-Request"
DASHBOARD_REQUEST_VALUE = "dashboard"

app = Flask(
    __name__,
    static_folder=str(DASHBOARD_DIRECTORY),
    static_url_path="",
)
app.json.ensure_ascii = False


def get_last_updated(dataframe):
    """取得資料庫最後新增新聞的時間。"""
    if dataframe.empty or "created_at" not in dataframe.columns:
        return None

    created_times = pd.to_datetime(
        dataframe["created_at"],
        errors="coerce",
    )
    last_updated = created_times.max()

    if pd.isna(last_updated):
        return None

    return last_updated.isoformat(timespec="seconds")


def attach_companies_to_news(records, company_links):
    """依內部 news id 合併公司資料，並在輸出前移除 news id。"""
    links_by_news_id = {}

    for link in company_links:
        news_id = link.get("news_id")
        company_id = link.get("company_id")

        if news_id is None or company_id is None:
            raise ValueError("新聞公司關聯缺少必要欄位。")

        company = {
            key: link.get(key)
            for key in [
                "company_id",
                "name",
                "short_name",
                "industry",
                "ticker",
                "exchange",
                "matched_text",
                "match_method",
                "confidence",
            ]
        }
        links_by_news_id.setdefault(news_id, []).append(company)

    for record in records:
        news_id = record.pop("id", None)
        record["companies"] = links_by_news_id.get(news_id, [])

    return records


def build_news_payload(dataframe, company_links=None):
    """將 MySQL DataFrame 轉成 API 新聞 response。"""
    if company_links is None:
        company_links = []

    balanced_dataframe = get_balanced_recent_news(dataframe)
    records = prepare_dashboard_records(
        balanced_dataframe,
        include_id=True,
    )
    records = attach_companies_to_news(records, company_links)
    records = group_similar_events(records)

    return {
        "count": len(records),
        "news": records,
    }


def build_analytics_payload(dataframe):
    """使用現有分析函式建立 Dashboard 統計 response。"""
    balanced_dataframe = get_balanced_recent_news(dataframe)
    records = prepare_dashboard_records(balanced_dataframe)
    chart_data = generate_chart_data(records)
    title_dataframe = create_title_dataframe(records)
    keyword_dataframe = count_top_keywords(title_dataframe)

    return {
        "sources": chart_data["sources"],
        "categories": chart_data["categories"],
        "keywords": keyword_dataframe.to_dict(orient="records"),
        "last_updated": get_last_updated(dataframe),
    }


def attach_dashboard_source_counts(source_summaries, dataframe):
    """以新聞列表的平衡資料集合取代來源原始解析筆數。"""
    balanced_dataframe = get_balanced_recent_news(dataframe)
    source_counts = balanced_dataframe["source"].value_counts().to_dict()

    for summary in source_summaries:
        summary["article_count"] = int(
            source_counts.get(summary["source"], 0)
        )

    return source_summaries


def database_error_response(error):
    """記錄內部錯誤，回傳不包含帳密與 SQL 的安全訊息。"""
    app.logger.error("Dashboard API 無法讀取資料：%s", error)
    return jsonify({
        "error": "無法讀取 Morning Alpha 新聞資料。",
    }), 500


def company_data_error_response(error):
    """回傳不包含 SQL 與連線細節的公司資料錯誤。"""
    app.logger.error("Dashboard API 無法讀取公司資料：%s", error)
    return jsonify({
        "error": "無法讀取 Morning Alpha 公司資料。",
    }), 500


@app.get("/api/health")
def health():
    """確認 Flask 服務本身可以回應。"""
    return jsonify({"status": "ok"})


@app.get("/")
def dashboard():
    """由 Flask 提供 Dashboard 首頁。"""
    return app.send_static_file("index.html")


@app.get("/api/news")
def news():
    """從 MySQL 讀取並回傳 Dashboard 新聞。"""
    try:
        dataframe = load_all_news()
        company_links = load_news_company_links()
        return jsonify(build_news_payload(dataframe, company_links))
    except (pymysql.MySQLError, ValueError) as error:
        return database_error_response(error)


@app.get("/api/analytics")
def analytics():
    """從 MySQL 新聞即時計算並回傳 Dashboard 統計。"""
    try:
        dataframe = load_all_news()
        return jsonify(build_analytics_payload(dataframe))
    except (pymysql.MySQLError, ValueError) as error:
        return database_error_response(error)


@app.get("/api/source-health")
def source_health():
    """回傳每個新聞來源最近一次執行與成功狀態。"""
    try:
        rows, columns = load_source_health_events()
        sources = build_source_health_summary(rows, columns)
        sources = attach_dashboard_source_counts(sources, load_all_news())
        return jsonify({"sources": sources})
    except (pymysql.MySQLError, ValueError) as error:
        return database_error_response(error)


@app.get("/api/pipeline-runs")
def pipeline_runs():
    """回傳最近十次完整 Pipeline 執行紀錄。"""
    try:
        rows, columns = load_pipeline_runs(limit=10)
        runs = build_pipeline_run_records(rows, columns)
        return jsonify({"runs": runs})
    except (json.JSONDecodeError, pymysql.MySQLError, ValueError) as error:
        return database_error_response(error)


@app.get("/api/pipeline/status")
def pipeline_status():
    """回傳由 Dashboard 啟動的 Pipeline subprocess 狀態。"""
    return jsonify({"pipeline": get_pipeline_status()})


@app.post("/api/pipeline/run")
def run_pipeline_from_dashboard():
    """在 API 所在環境啟動 Pipeline，並阻止重複執行。"""
    if request.headers.get(DASHBOARD_REQUEST_HEADER) != DASHBOARD_REQUEST_VALUE:
        return jsonify({"error": "只接受 Morning Alpha Dashboard 的請求。"}), 403

    try:
        started, status = start_pipeline()
    except OSError as error:
        app.logger.error("Dashboard 無法啟動 Pipeline：%s", error)
        return jsonify({"error": "無法啟動 Morning Alpha Pipeline。"}), 500

    response_status = 202 if started else 409
    return jsonify({"pipeline": status}), response_status


@app.get("/api/daily-briefs/latest")
def latest_daily_brief():
    """回傳最新一份每日晨報；尚無資料時回傳 null。"""
    try:
        briefs = load_daily_briefs(limit=1)
        brief = briefs[0] if briefs else None
        return jsonify({"brief": brief})
    except (json.JSONDecodeError, pymysql.MySQLError, ValueError) as error:
        return database_error_response(error)


@app.get("/api/daily-briefs")
def daily_briefs():
    """回傳最近三十份歷史晨報。"""
    try:
        briefs = load_daily_briefs(limit=30)
        return jsonify({"briefs": briefs})
    except (json.JSONDecodeError, pymysql.MySQLError, ValueError) as error:
        return database_error_response(error)


@app.get("/api/company-news-links")
def company_news_links():
    """回傳新聞公司關聯，可選擇以 company_id 篩選。"""
    company_id_value = request.args.get("company_id")

    try:
        company_id = None

        if company_id_value is not None:
            try:
                company_id = int(company_id_value)
            except ValueError as error:
                raise ValueError("company_id 必須是正整數。") from error

            if company_id <= 0:
                raise ValueError("company_id 必須是正整數。")

        links = load_news_company_links(company_id=company_id)
        return jsonify({"links": links})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except pymysql.MySQLError as error:
        return database_error_response(error)


@app.get("/api/market-companies")
def market_companies():
    """回傳已有價格或財務資料的公司清單。"""
    try:
        return jsonify({"companies": load_market_companies()})
    except (pymysql.MySQLError, ValueError) as error:
        return company_data_error_response(error)


@app.get("/api/companies/<int:company_id>/market-prices")
def company_market_prices(company_id):
    """回傳指定公司最近九十筆每日價格。"""
    try:
        prices = load_company_market_prices(company_id, limit=90)
        return jsonify({"prices": prices})
    except (pymysql.MySQLError, ValueError) as error:
        return company_data_error_response(error)


@app.get("/api/companies/<int:company_id>/financial-metrics")
def company_financial_metrics(company_id):
    """回傳指定公司最近八季財務摘要。"""
    try:
        metrics = load_company_financial_metrics(company_id, limit=8)
        return jsonify({"metrics": metrics})
    except (pymysql.MySQLError, ValueError) as error:
        return company_data_error_response(error)


@app.get("/api/event-market-observations")
def event_market_observations():
    """回傳新聞事件附近的收盤價時間關聯，不宣稱因果。"""
    try:
        observations, readiness = load_event_market_analysis(limit=20)
        return jsonify({
            "analysis_type": ANALYSIS_TYPE,
            "methodology": EVENT_MARKET_METHODOLOGY,
            "limitations": EVENT_MARKET_LIMITATIONS,
            "observations": observations,
            "readiness": readiness,
        })
    except (KeyError, pymysql.MySQLError, ValueError) as error:
        return company_data_error_response(error)


@app.get("/api/watchlist")
def watchlist():
    """回傳本機單一使用者的公司追蹤清單。"""
    try:
        return jsonify({"items": load_watchlist()})
    except (pymysql.MySQLError, ValueError) as error:
        return company_data_error_response(error)


@app.post("/api/watchlist/<int:company_id>")
def add_watchlist_item(company_id):
    """將指定公司加入追蹤清單；重複加入保持相同狀態。"""
    try:
        added = add_watchlist_company(company_id)
        return jsonify({
            "company_id": company_id,
            "added": added,
        }), 201 if added else 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except pymysql.MySQLError as error:
        return company_data_error_response(error)


@app.delete("/api/watchlist/<int:company_id>")
def delete_watchlist_item(company_id):
    """將指定公司移出追蹤清單；不存在時保持相同狀態。"""
    try:
        removed = remove_watchlist_company(company_id)
        return jsonify({
            "company_id": company_id,
            "removed": removed,
        })
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except pymysql.MySQLError as error:
        return company_data_error_response(error)


@app.get("/api/personalized-brief")
def personalized_brief():
    """即時計算最新時間窗的追蹤公司個人化晨報。"""
    try:
        return jsonify({"brief": load_personalized_brief()})
    except (KeyError, pymysql.MySQLError, ValueError) as error:
        return company_data_error_response(error)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
