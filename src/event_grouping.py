"""使用標題斷詞與發布時間，將相似新聞標記為同一事件。"""

import hashlib
from datetime import datetime, timedelta
import unicodedata

from analyze_keywords import extract_keywords


DEFAULT_SIMILARITY_THRESHOLD = 0.35
DEFAULT_MIN_SHARED_KEYWORDS = 2
DEFAULT_TIME_WINDOW_HOURS = 72
SAME_TITLE_REASON = "same_normalized_title"
SIMILAR_EVENT_REASON = "similar_event"


def normalize_title(title):
    """移除大小寫、全半形、空白與標點差異，供標題識別使用。"""
    normalized_title = unicodedata.normalize(
        "NFKC",
        str(title or ""),
    ).casefold()
    return "".join(
        character
        for character in normalized_title
        if character.isalnum()
    )


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


def articles_are_within_time_window(
    first_article,
    second_article,
    time_window_hours=DEFAULT_TIME_WINDOW_HOURS,
):
    """確認兩篇文章時間有效，且位於指定小時範圍內。"""
    first_time = parse_publish_time(first_article.get("publish_time"))
    second_time = parse_publish_time(second_article.get("publish_time"))

    if first_time is None or second_time is None:
        return False

    time_difference = abs(first_time - second_time)
    return time_difference <= timedelta(hours=time_window_hours)


def has_same_normalized_title(first_article, second_article):
    """判斷兩篇文章是否只有標點、空白或全半形差異。"""
    first_title = normalize_title(first_article.get("title"))
    second_title = normalize_title(second_article.get("title"))

    if not first_title or not second_title:
        return False

    return first_title == second_title


def is_similar_event(
    first_article,
    second_article,
    similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD,
    min_shared_keywords=DEFAULT_MIN_SHARED_KEYWORDS,
    time_window_hours=DEFAULT_TIME_WINDOW_HOURS,
):
    """判斷兩篇新聞是否可能描述同一事件。"""
    if not articles_are_within_time_window(
        first_article,
        second_article,
        time_window_hours=time_window_hours,
    ):
        return False

    first_keywords = set(extract_keywords(first_article.get("title", "")))
    second_keywords = set(extract_keywords(second_article.get("title", "")))
    shared_keywords = first_keywords & second_keywords

    if len(shared_keywords) < min_shared_keywords:
        return False

    similarity = calculate_similarity(first_keywords, second_keywords)
    return similarity >= similarity_threshold


def identify_article_relationship(first_article, second_article):
    """依可信程度回傳同標題或相似事件關係。"""
    if not articles_are_within_time_window(first_article, second_article):
        return None

    if has_same_normalized_title(first_article, second_article):
        return SAME_TITLE_REASON

    if is_similar_event(first_article, second_article):
        return SIMILAR_EVENT_REASON

    return None


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
        grouped_record["event_group_reason"] = None
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
        matched_reason = None

        for group in groups:
            for member_index in group["members"]:
                relationship = identify_article_relationship(
                    record,
                    grouped_records[member_index],
                )

                if relationship is not None:
                    matched_group = group
                    matched_reason = relationship
                    break

            if matched_group is not None:
                break

        if matched_group is None:
            groups.append({
                "members": [record_index],
                "reasons": set(),
            })
        else:
            matched_group["members"].append(record_index)
            matched_group["reasons"].add(matched_reason)

    for group in groups:
        members = group["members"]

        if len(members) < 2:
            continue

        group_id = create_event_group_id(grouped_records[members[0]])
        group_reason = SAME_TITLE_REASON

        if SIMILAR_EVENT_REASON in group["reasons"]:
            group_reason = SIMILAR_EVENT_REASON

        for record_index in members:
            grouped_records[record_index]["event_group_id"] = group_id
            grouped_records[record_index]["event_group_size"] = len(members)
            grouped_records[record_index]["event_group_reason"] = group_reason

    return grouped_records
