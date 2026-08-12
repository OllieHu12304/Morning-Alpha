"""定義不同新聞來源共同使用的文章資料格式。"""

from datetime import datetime


NEWS_RECORD_FIELDS = (
    "source",
    "publisher",
    "source_article_id",
    "source_category",
    "title",
    "publish_time",
    "url",
)


def create_news_record(
    source,
    source_category,
    title,
    publish_time,
    url,
    publisher=None,
    source_article_id=None,
):
    """驗證欄位並建立一筆來源無關的新聞 dict。"""
    required_text_fields = {
        "source": source,
        "title": title,
        "url": url,
    }

    for field_name, value in required_text_fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} 必須是非空白文字。")

    if publisher is None:
        publisher = source

    if not isinstance(publisher, str) or not publisher.strip():
        raise ValueError("publisher 必須是非空白文字。")

    if source_article_id is not None:
        if not isinstance(source_article_id, str):
            raise ValueError("source_article_id 必須是文字或 None。")

        source_article_id = source_article_id.strip() or None

    if source_category is not None:
        if not isinstance(source_category, str):
            raise ValueError("source_category 必須是文字或 None。")

        source_category = source_category.strip() or None

    if not isinstance(publish_time, datetime):
        raise ValueError("publish_time 必須是 datetime。")

    return {
        "source": source.strip(),
        "publisher": publisher.strip(),
        "source_article_id": source_article_id,
        "source_category": source_category,
        "title": title.strip(),
        "publish_time": publish_time,
        "url": url.strip(),
    }


def validate_news_record(record):
    """確認既有 dict 完整符合共同格式，並回傳整理後的副本。"""
    if not isinstance(record, dict):
        raise ValueError("新聞資料必須是 dict。")

    missing_fields = []

    for field_name in NEWS_RECORD_FIELDS:
        if field_name not in record:
            missing_fields.append(field_name)

    if missing_fields:
        field_list = ", ".join(missing_fields)
        raise ValueError(f"新聞資料缺少欄位：{field_list}。")

    return create_news_record(
        source=record["source"],
        source_category=record["source_category"],
        title=record["title"],
        publish_time=record["publish_time"],
        url=record["url"],
        publisher=record["publisher"],
        source_article_id=record["source_article_id"],
    )
