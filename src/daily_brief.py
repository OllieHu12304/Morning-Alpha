"""使用現有新聞分析結果建立可重現的結構化每日晨報。"""

from datetime import date, datetime

from daily_brief_window import get_brief_window, to_database_datetime
from event_grouping import group_similar_events
from generate_chart_data import generate_chart_data


HIGHLIGHT_LIMIT = 5
SUMMARY_ITEM_LIMIT = 3
KEYWORD_LIMIT = 5
BRIEF_LIMITATIONS = [
    "摘要只根據新聞標題與來源欄位產生，沒有分析文章全文。",
    "事件分組與分類是規則式推論，可能漏判或誤判。",
    "本摘要不構成投資建議。",
]


def parse_record_time(value):
    """將新聞 record 的 ISO 時間轉成可比較的 naive datetime。"""
    if isinstance(value, datetime):
        parsed_time = value
    else:
        try:
            parsed_time = datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    if parsed_time.tzinfo is not None:
        return to_database_datetime(parsed_time)

    return parsed_time


def select_brief_records(records, brief_date):
    """選出指定晨報固定時間窗內的新聞。"""
    if not isinstance(records, list):
        raise ValueError("records 必須是 list。")

    if any(not isinstance(record, dict) for record in records):
        raise ValueError("每一筆新聞資料都必須是 object。")

    start_time, end_time = get_brief_window(brief_date)
    database_start = to_database_datetime(start_time)
    database_end = to_database_datetime(end_time)
    selected_records = []

    for record in records:
        publish_time = parse_record_time(record.get("publish_time"))

        if publish_time is None:
            continue

        if database_start <= publish_time < database_end:
            selected_records.append(dict(record))

    return selected_records


def chart_group_to_items(chart_group, limit):
    """將 Chart.js labels/values 轉成晨報容易閱讀的 records。"""
    labels = chart_group.get("labels", [])
    values = chart_group.get("values", [])
    items = []

    for label, value in zip(labels, values):
        items.append({"name": label, "count": int(value)})

        if len(items) == limit:
            break

    return items


def build_highlights(records, limit=HIGHLIGHT_LIMIT):
    """依同事件文章數與發布時間選出晨報 highlights。"""
    grouped_records = group_similar_events(records)
    sorted_records = sorted(
        grouped_records,
        key=lambda record: (
            int(record.get("event_group_size", 1)),
            parse_record_time(record.get("publish_time")) or datetime.min,
        ),
        reverse=True,
    )
    highlights = []

    for record in sorted_records[:limit]:
        group_size = int(record.get("event_group_size", 1))
        selection_reason = "時間窗內最新文章"

        if group_size > 1:
            selection_reason = f"同事件共有 {group_size} 篇報導"

        highlights.append({
            "title": str(record.get("title", "")),
            "source": record.get("source"),
            "analysis_category": record.get("analysis_category"),
            "publish_time": record.get("publish_time"),
            "url": record.get("url"),
            "event_group_id": record.get("event_group_id"),
            "event_group_size": group_size,
            "selection_reason": selection_reason,
        })

    return highlights


def get_leading_name(items, empty_label):
    """取得統計第一名，無資料時使用清楚的替代文字。"""
    if not items:
        return empty_label

    return items[0]["name"]


def build_summary_text(article_count, sources, categories, keywords):
    """使用固定模板產生不含額外推測的摘要文字。"""
    if article_count == 0:
        return "本期時間窗內沒有可用新聞。"

    leading_source = get_leading_name(sources, "未知來源")
    leading_category = get_leading_name(categories, "未分類")
    leading_keyword = get_leading_name(keywords, "無明顯關鍵字")
    return (
        f"本期共收錄 {article_count} 篇新聞，"
        f"主要來源為{leading_source}，"
        f"最多的分析分類為{leading_category}，"
        f"最常見關鍵字為{leading_keyword}。"
    )


def build_daily_brief(records, brief_date):
    """建立指定日期的完整結構化晨報。"""
    if not isinstance(brief_date, date) or isinstance(brief_date, datetime):
        raise ValueError("brief_date 必須是 date。")

    selected_records = select_brief_records(records, brief_date)
    start_time, end_time = get_brief_window(brief_date)
    chart_data = generate_chart_data(selected_records)
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
    article_count = len(selected_records)

    return {
        "brief_date": brief_date.isoformat(),
        "window_start": start_time.isoformat(timespec="seconds"),
        "window_end": end_time.isoformat(timespec="seconds"),
        "article_count": article_count,
        "summary": build_summary_text(
            article_count,
            sources,
            categories,
            keywords,
        ),
        "sources": sources,
        "categories": categories,
        "keywords": keywords,
        "highlights": build_highlights(selected_records),
        "limitations": list(BRIEF_LIMITATIONS),
    }
