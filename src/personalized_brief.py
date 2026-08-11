"""依追蹤公司與新聞關聯建立即時個人化晨報。"""

import pymysql

from daily_brief import build_daily_brief
from daily_brief_window import get_latest_brief_date
from store_news import connect_to_database, get_database_config
from watchlist import fetch_watchlist


PERSONALIZED_BRIEF_LIMITATIONS = [
    "個人化晨報只收錄標題規則成功連結至追蹤公司的新聞。",
    "沒有比對到公司不代表事件與該公司無關。",
]

READ_WATCHLIST_NEWS_SQL = """
SELECT
    news_records.id,
    news_records.source,
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


def build_personalized_brief(records, brief_date, watchlist_items):
    """建立只計入追蹤公司相關新聞的結構化晨報。"""
    if not isinstance(watchlist_items, list):
        raise ValueError("watchlist_items 必須是 list。")

    brief = build_daily_brief(records, brief_date)
    brief["watchlist_count"] = len(watchlist_items)
    brief["watched_companies"] = watchlist_items
    attach_highlight_companies(brief["highlights"], records)
    brief["limitations"].extend(PERSONALIZED_BRIEF_LIMITATIONS)

    if not watchlist_items:
        brief["summary"] = "尚未加入追蹤公司，請先從公司市場資料加入。"
    elif brief["article_count"] == 0:
        brief["summary"] = (
            f"目前追蹤 {len(watchlist_items)} 家公司，"
            "本期時間窗內沒有成功連結的相關新聞。"
        )
    else:
        brief["summary"] = (
            f"目前追蹤 {len(watchlist_items)} 家公司，"
            f"本期找到 {brief['article_count']} 篇相關新聞。"
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
