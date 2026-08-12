"""保存並讀取新聞來源的擷取健康狀態。"""

from datetime import datetime, timezone

import pymysql

from store_news import connect_to_database, get_database_config


MAX_ERROR_LENGTH = 500
VALID_STATUSES = {"success", "failure"}

CREATE_SOURCE_HEALTH_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS source_health_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    article_count INT UNSIGNED NOT NULL DEFAULT 0,
    error_message VARCHAR(500) NULL,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX index_source_attempted_at (source, attempted_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

INSERT_SOURCE_HEALTH_SQL = """
INSERT INTO source_health_events (
    source,
    status,
    article_count,
    error_message
)
VALUES (%s, %s, %s, %s);
"""

READ_SOURCE_HEALTH_SQL = """
SELECT
    source,
    status,
    article_count,
    error_message,
    attempted_at,
    UNIX_TIMESTAMP(attempted_at) AS attempted_at_epoch
FROM source_health_events
ORDER BY attempted_at DESC, id DESC;
"""


def prepare_source_health_records(source_results):
    """驗證來源結果並轉成 PyMySQL records。"""
    records = []

    for result in source_results:
        source = result.get("source")
        status = result.get("status")
        article_count = result.get("article_count", 0)
        error_message = result.get("error_message")

        if not source or status not in VALID_STATUSES:
            raise ValueError("來源健康狀態包含無效的 source 或 status。")

        if not isinstance(article_count, int) or article_count < 0:
            raise ValueError("來源健康狀態的 article_count 必須是非負整數。")

        if status == "success":
            error_message = None
        elif error_message:
            error_message = " ".join(str(error_message).split())
            error_message = error_message[:MAX_ERROR_LENGTH]
        else:
            error_message = "未知來源錯誤"

        records.append((
            source,
            status,
            article_count,
            error_message,
        ))

    return records


def create_source_health_table(connection):
    """建立 append-only source health events table。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_SOURCE_HEALTH_TABLE_SQL)


def insert_source_health_events(connection, source_results):
    """將一次來源擷取結果寫成 events。"""
    records = prepare_source_health_records(source_results)

    if not records:
        return 0

    with connection.cursor() as cursor:
        return cursor.executemany(INSERT_SOURCE_HEALTH_SQL, records)


def save_source_health_events(source_results):
    """以獨立 transaction 保存來源擷取結果。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_source_health_table(connection)
        inserted_count = insert_source_health_events(
            connection,
            source_results,
        )
        connection.commit()
        return inserted_count
    except (pymysql.MySQLError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_source_health_events(connection):
    """依最新到最舊讀取全部 source health events。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_SOURCE_HEALTH_SQL)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return rows, column_names


def load_source_health_events():
    """連接 MySQL 並讀取 source health events。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return fetch_source_health_events(connection)
    finally:
        connection.close()


def format_timestamp(epoch_seconds):
    """使用不受 MySQL session timezone 影響的 epoch 建立 UTC 時間。"""
    if isinstance(epoch_seconds, (int, float)):
        utc_value = datetime.fromtimestamp(
            epoch_seconds,
            tz=timezone.utc,
        )
        return utc_value.isoformat(timespec="seconds")

    return None


def build_source_health_summary(rows, column_names):
    """整理每個來源的最近狀態與最近成功時間。"""
    events = []

    for row in rows:
        events.append(dict(zip(column_names, row)))

    latest_by_source = {}
    last_success_by_source = {}

    for event in events:
        source = event["source"]

        if source not in latest_by_source:
            latest_by_source[source] = event

        if event["status"] == "success" and source not in last_success_by_source:
            last_success_by_source[source] = event["attempted_at_epoch"]

    summaries = []

    for source in sorted(latest_by_source):
        latest = latest_by_source[source]
        summaries.append({
            "source": source,
            "status": latest["status"],
            "article_count": latest["article_count"],
            "error_message": latest["error_message"],
            "last_attempt_at": format_timestamp(
                latest["attempted_at_epoch"]
            ),
            "last_success_at": format_timestamp(
                last_success_by_source.get(source)
            ),
        })

    return summaries
