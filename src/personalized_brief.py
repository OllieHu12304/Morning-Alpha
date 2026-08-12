"""依追蹤公司與新聞關聯建立即時個人化晨報。"""

from datetime import datetime, time

import pymysql

from daily_brief import (
    KEYWORD_LIMIT,
    SUMMARY_ITEM_LIMIT,
    BRIEF_LIMITATIONS,
    build_highlights,
    build_summary_text,
    chart_group_to_items,
    parse_record_time,
)
from daily_brief_window import get_latest_brief_date
from generate_chart_data import generate_chart_data
from store_news import connect_to_database, get_database_config
from watchlist import fetch_watchlist


PERSONALIZED_BRIEF_LIMITATIONS = [
    "個人化晨報只收錄標題規則成功連結至追蹤公司的新聞。",
    "沒有比對到公司不代表事件與該公司無關。",
    "每家追蹤公司最多顯示最近 5 篇成功連結的新聞。",
]
RECENT_NEWS_PER_COMPANY = 5

READ_WATCHLIST_NEWS_SQL = """
SELECT
    news_records.id,
    news_records.source,
    news_records.publisher,
    news_records.source_article_id,
    news_records.source_category,
    news_records.analysis_category,
    news_records.title,
    news_records.publish_time,
    news_records.url,
    news_company_links.company_id,
    companies.name AS company_name,
    companies.short_name,
    securities.ticker
FROM watchlist_items
JOIN companies ON companies.id = watchlist_items.company_id
JOIN news_company_links
    ON news_company_links.company_id = watchlist_items.company_id
JOIN news_records ON news_records.id = news_company_links.news_id
LEFT JOIN securities ON securities.id = (
    SELECT MIN(active_security.id)
    FROM securities AS active_security
    WHERE active_security.company_id = companies.id
        AND active_security.is_active = TRUE
)
ORDER BY news_records.publish_time DESC, news_records.id DESC;
"""


def build_related_news_records(rows, column_names):
    """合併同一則新聞的多個追蹤公司，避免文章重複計數。"""
    records_by_id = {}

    for row in rows:
        source_record = dict(zip(column_names, row))
        news_id = source_record["id"]

        if news_id not in records_by_id:
            records_by_id[news_id] = {
                "id": news_id,
                "source": source_record["source"],
                "publisher": source_record["publisher"],
                "source_article_id": source_record["source_article_id"],
                "source_category": source_record["source_category"],
                "analysis_category": source_record["analysis_category"],
                "title": source_record["title"],
                "publish_time": source_record["publish_time"],
                "url": source_record["url"],
                "companies": [],
            }

        company = {
            "company_id": source_record["company_id"],
            "name": source_record["company_name"],
            "short_name": source_record["short_name"],
            "ticker": source_record["ticker"],
        }

        if company not in records_by_id[news_id]["companies"]:
            records_by_id[news_id]["companies"].append(company)

    return list(records_by_id.values())


def fetch_watchlist_news(connection):
    """讀取已與追蹤公司建立關聯的新聞。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_WATCHLIST_NEWS_SQL)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return build_related_news_records(rows, column_names)


def attach_highlight_companies(highlights, records):
    """將個人化新聞中的公司標籤附加到晨報 highlights。"""
    companies_by_news = {
        (record.get("url"), record.get("title")): record.get("companies", [])
        for record in records
    }

    for highlight in highlights:
        key = (highlight.get("url"), highlight.get("title"))
        highlight["companies"] = companies_by_news.get(key, [])


def select_recent_company_news(records, per_company_limit=RECENT_NEWS_PER_COMPANY):
    """每家公司保留最新數筆新聞，再合併重複文章。"""
    if not isinstance(per_company_limit, int) or per_company_limit < 1:
        raise ValueError("per_company_limit 必須是正整數。")

    sorted_records = sorted(
        records,
        key=lambda record: parse_record_time(record.get("publish_time"))
        or datetime.min,
        reverse=True,
    )
    company_counts = {}
    selected_by_id = {}

    for record in sorted_records:
        include_record = False

        for company in record.get("companies", []):
            company_id = company.get("company_id")
            current_count = company_counts.get(company_id, 0)

            if company_id is not None and current_count < per_company_limit:
                company_counts[company_id] = current_count + 1
                include_record = True

        if include_record:
            selected_by_id[record["id"]] = dict(record)

    return list(selected_by_id.values())


def build_recent_news_brief(records, brief_date):
    """將近期追蹤新聞整理成與 Dashboard 相容的摘要格式。"""
    chart_data = generate_chart_data(records)
    sources = chart_group_to_items(
        chart_data["sources"],
        SUMMARY_ITEM_LIMIT,
    )
    categories = chart_group_to_items(
        chart_data["categories"],
        SUMMARY_ITEM_LIMIT,
    )
    keywords = chart_group_to_items(
        chart_data["keywords"],
        KEYWORD_LIMIT,
    )
    record_times = [
        parse_record_time(record.get("publish_time"))
        for record in records
    ]
    record_times = [value for value in record_times if value is not None]
    fallback_time = datetime.combine(brief_date, time.min)
    window_start = min(record_times, default=fallback_time)
    window_end = max(record_times, default=fallback_time)

    return {
        "brief_date": brief_date.isoformat(),
        "window_start": window_start.isoformat(timespec="seconds"),
        "window_end": window_end.isoformat(timespec="seconds"),
        "article_count": len(records),
        "summary": build_summary_text(
            len(records),
            sources,
            categories,
            keywords,
        ),
        "sources": sources,
        "categories": categories,
        "keywords": keywords,
        "highlights": build_highlights(records, limit=len(records)),
        "limitations": list(BRIEF_LIMITATIONS),
    }


def build_personalized_brief(records, brief_date, watchlist_items):
    """建立每家追蹤公司近期相關新聞摘要。"""
    if not isinstance(watchlist_items, list):
        raise ValueError("watchlist_items 必須是 list。")

    recent_records = select_recent_company_news(records)
    brief = build_recent_news_brief(recent_records, brief_date)
    brief["watchlist_count"] = len(watchlist_items)
    brief["watched_companies"] = watchlist_items
    attach_highlight_companies(brief["highlights"], recent_records)
    brief["limitations"].extend(PERSONALIZED_BRIEF_LIMITATIONS)

    if not watchlist_items:
        brief["summary"] = "尚未加入追蹤公司，請先搜尋公司並加入追蹤。"
    elif brief["article_count"] == 0:
        brief["summary"] = (
            f"目前追蹤 {len(watchlist_items)} 家公司，"
            "目前沒有成功連結的相關新聞。"
        )
    else:
        brief["summary"] = (
            f"目前追蹤 {len(watchlist_items)} 家公司，"
            f"找到 {brief['article_count']} 篇近期相關新聞。"
        )

    return brief


def load_personalized_brief(brief_date=None):
    """從 MySQL 讀取追蹤清單與相關新聞並建立最新晨報。"""
    if brief_date is None:
        brief_date = get_latest_brief_date()

    config = get_database_config()
    connection = connect_to_database(config)

    try:
        watchlist_items = fetch_watchlist(connection)
        records = fetch_watchlist_news(connection) if watchlist_items else []
        return build_personalized_brief(
            records,
            brief_date,
            watchlist_items,
        )
    except (KeyError, pymysql.MySQLError, ValueError):
        raise
    finally:
        connection.close()
