"""使用標題斷詞與發布時間，將相似新聞標記為同一事件。"""

import hashlib
from datetime import datetime, timedelta

from analyze_keywords import extract_keywords


DEFAULT_SIMILARITY_THRESHOLD = 0.35
DEFAULT_MIN_SHARED_KEYWORDS = 2
DEFAULT_TIME_WINDOW_HOURS = 72


def calculate_similarity(first_keywords, second_keywords):
    """計算兩組關鍵字的 Jaccard similarity。"""
    union = first_keywords | second_keywords

    if not union:
        return 0.0

    intersection = first_keywords & second_keywords
    return len(intersection) / len(union)


def parse_publish_time(value):
    """將 news.json 的 ISO 時間轉成 datetime。"""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def is_similar_event(
    first_article,
    second_article,
    similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD,
    min_shared_keywords=DEFAULT_MIN_SHARED_KEYWORDS,
    time_window_hours=DEFAULT_TIME_WINDOW_HOURS,
):
    """判斷兩篇新聞是否可能描述同一事件。"""
    first_time = parse_publish_time(first_article.get("publish_time"))
    second_time = parse_publish_time(second_article.get("publish_time"))

    if first_time is None or second_time is None:
        return False

    time_difference = abs(first_time - second_time)

    if time_difference > timedelta(hours=time_window_hours):
        return False

    first_keywords = set(extract_keywords(first_article.get("title", "")))
    second_keywords = set(extract_keywords(second_article.get("title", "")))
    shared_keywords = first_keywords & second_keywords

    if len(shared_keywords) < min_shared_keywords:
        return False

    similarity = calculate_similarity(first_keywords, second_keywords)
    return similarity >= similarity_threshold


def create_event_group_id(seed_article):
    """使用第一篇文章的穩定內容建立簡短 event ID。"""
    identity = "|".join([
        str(seed_article.get("source", "")),
        str(seed_article.get("title", "")),
        str(seed_article.get("publish_time", "")),
    ])
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    return f"event-{digest}"


def group_similar_events(records):
    """回傳加入 event_group_id 與 event_group_size 的新聞副本。"""
    grouped_records = []

    for record in records:
        grouped_record = dict(record)
        grouped_record["event_group_id"] = None
        grouped_record["event_group_size"] = 1
        grouped_records.append(grouped_record)

    sorted_indexes = sorted(
        range(len(grouped_records)),
        key=lambda index: (
            parse_publish_time(grouped_records[index].get("publish_time"))
            or datetime.min
        ),
    )
    groups = []

    for record_index in sorted_indexes:
        record = grouped_records[record_index]
        matched_group = None

        for group in groups:
            if any(
                is_similar_event(record, grouped_records[member_index])
                for member_index in group
            ):
                matched_group = group
                break

        if matched_group is None:
            groups.append([record_index])
        else:
            matched_group.append(record_index)

    for group in groups:
        if len(group) < 2:
            continue

        group_id = create_event_group_id(grouped_records[group[0]])

        for record_index in group:
            grouped_records[record_index]["event_group_id"] = group_id
            grouped_records[record_index]["event_group_size"] = len(group)

    return grouped_records
