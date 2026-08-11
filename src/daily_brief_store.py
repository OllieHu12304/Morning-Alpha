"""將結構化每日晨報保存到 MySQL。"""

import json
from datetime import date, datetime

import pymysql

from daily_brief_window import to_database_datetime
from store_news import connect_to_database, get_database_config


CREATE_DAILY_BRIEFS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS daily_briefs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brief_date DATE NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    article_count INT UNSIGNED NOT NULL,
    brief_payload JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_daily_brief_date (brief_date),
    INDEX index_daily_brief_updated_at (updated_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

UPSERT_DAILY_BRIEF_SQL = """
INSERT INTO daily_briefs (
    brief_date,
    window_start,
    window_end,
    article_count,
    brief_payload
)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    window_start = VALUES(window_start),
    window_end = VALUES(window_end),
    article_count = VALUES(article_count),
    brief_payload = VALUES(brief_payload);
"""

READ_DAILY_BRIEFS_SQL = """
SELECT brief_payload
FROM daily_briefs
ORDER BY brief_date DESC
LIMIT %s;
"""


def create_daily_briefs_table(connection):
    """建立每日晨報 table。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_DAILY_BRIEFS_TABLE_SQL)


def parse_iso_datetime(value, field_name):
    """解析晨報 ISO 時間並轉成 MySQL 台北時間。"""
    try:
        parsed_value = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} 必須是 ISO datetime。") from error

    if parsed_value.tzinfo is None:
        raise ValueError(f"{field_name} 必須包含 timezone。")

    return to_database_datetime(parsed_value)


def prepare_daily_brief_record(brief):
    """驗證晨報並建立 parameterized SQL record。"""
    if not isinstance(brief, dict):
        raise ValueError("brief 必須是 object。")

    try:
        brief_date = date.fromisoformat(str(brief["brief_date"]))
        article_count = int(brief["article_count"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("晨報缺少有效日期或文章數。") from error

    if article_count < 0:
        raise ValueError("article_count 不可小於 0。")

    window_start = parse_iso_datetime(
        brief.get("window_start"),
        "window_start",
    )
    window_end = parse_iso_datetime(
        brief.get("window_end"),
        "window_end",
    )

    if window_start >= window_end:
        raise ValueError("晨報時間窗的開始必須早於結束。")

    brief_payload = json.dumps(brief, ensure_ascii=False)
    return (
        brief_date,
        window_start,
        window_end,
        article_count,
        brief_payload,
    )


def upsert_daily_brief(connection, brief):
    """新增晨報；同一日期存在時更新原紀錄。"""
    record = prepare_daily_brief_record(brief)

    with connection.cursor() as cursor:
        cursor.execute(UPSERT_DAILY_BRIEF_SQL, record)
        return cursor.rowcount


def save_daily_brief(brief):
    """使用獨立 transaction 保存一份晨報。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_daily_briefs_table(connection)
        changed_count = upsert_daily_brief(connection, brief)
        connection.commit()
        return changed_count
    except (pymysql.MySQLError, TypeError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def decode_brief_payload(value):
    """將 MySQL JSON 欄位轉回 Python dict。"""
    if isinstance(value, dict):
        return value

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    payload = json.loads(value)

    if not isinstance(payload, dict):
        raise ValueError("daily brief payload 必須是 object。")

    return payload


def fetch_daily_briefs(connection, limit=30):
    """讀取最近的歷史晨報。"""
    if not isinstance(limit, int) or limit < 1 or limit > 365:
        raise ValueError("daily brief limit 必須介於 1 到 365。")

    with connection.cursor() as cursor:
        cursor.execute(READ_DAILY_BRIEFS_SQL, (limit,))
        rows = cursor.fetchall()

    return [decode_brief_payload(row[0]) for row in rows]


def load_daily_briefs(limit=30):
    """連接 MySQL 並讀取最近的歷史晨報。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return fetch_daily_briefs(connection, limit=limit)
    finally:
        connection.close()
