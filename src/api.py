"""提供 Morning Alpha Dashboard 使用的 MySQL API。"""

import json
from pathlib import Path

import pandas as pd
import pymysql
from flask import Flask, jsonify

from analyze_keywords import count_top_keywords, create_title_dataframe
from daily_brief_store import load_daily_briefs
from event_grouping import group_similar_events
from export_news_json import prepare_dashboard_records
from generate_chart_data import generate_chart_data
from pipeline_history import build_pipeline_run_records, load_pipeline_runs
from read_news import load_all_news
from source_health import build_source_health_summary, load_source_health_events


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"

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


def build_news_payload(dataframe):
    """將 MySQL DataFrame 轉成 API 新聞 response。"""
    records = prepare_dashboard_records(dataframe)
    records = group_similar_events(records)

    return {
        "count": len(records),
        "news": records,
    }


def build_analytics_payload(dataframe):
    """使用現有分析函式建立 Dashboard 統計 response。"""
    records = prepare_dashboard_records(dataframe)
    chart_data = generate_chart_data(records)
    title_dataframe = create_title_dataframe(records)
    keyword_dataframe = count_top_keywords(title_dataframe)

    return {
        "sources": chart_data["sources"],
        "categories": chart_data["categories"],
        "keywords": keyword_dataframe.to_dict(orient="records"),
        "last_updated": get_last_updated(dataframe),
    }


def database_error_response(error):
    """記錄內部錯誤，回傳不包含帳密與 SQL 的安全訊息。"""
    app.logger.error("Dashboard API 無法讀取資料：%s", error)
    return jsonify({
        "error": "無法讀取 Morning Alpha 新聞資料。",
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
        return jsonify(build_news_payload(dataframe))
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
