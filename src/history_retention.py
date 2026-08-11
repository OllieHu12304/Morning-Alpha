"""清理超過保留期限的來源與 Pipeline 歷史紀錄。"""

import os
from datetime import timedelta

import pymysql

from pipeline_history import utc_now
from store_news import (
    connect_to_database,
    get_database_config,
    load_environment,
)


DEFAULT_RETENTION_DAYS = 90
MAX_RETENTION_DAYS = 3650

DELETE_OLD_SOURCE_HEALTH_SQL = """
DELETE FROM source_health_events
WHERE attempted_at < %s;
"""

DELETE_OLD_PIPELINE_RUNS_SQL = """
DELETE FROM pipeline_runs
WHERE started_at < %s;
"""


def get_retention_days():
    """讀取 1 到 3650 天的 history 保留期限。"""
    load_environment()
    retention_text = os.getenv(
        "HISTORY_RETENTION_DAYS",
        str(DEFAULT_RETENTION_DAYS),
    )

    try:
        retention_days = int(retention_text)
    except ValueError as error:
        raise ValueError(
            "HISTORY_RETENTION_DAYS 必須是整數。"
        ) from error

    if retention_days < 1 or retention_days > MAX_RETENTION_DAYS:
        raise ValueError(
            f"HISTORY_RETENTION_DAYS 必須介於 1 到 {MAX_RETENTION_DAYS}。"
        )

    return retention_days


def get_retention_cutoff(retention_days):
    """計算 UTC 保留期限分界。"""
    return utc_now() - timedelta(days=retention_days)


def delete_old_history(connection, cutoff):
    """只刪除兩張 history tables 中早於 cutoff 的紀錄。"""
    with connection.cursor() as cursor:
        cursor.execute("SET time_zone = '+00:00';")

        cursor.execute(DELETE_OLD_SOURCE_HEALTH_SQL, (cutoff,))
        deleted_source_events = cursor.rowcount

        cursor.execute(DELETE_OLD_PIPELINE_RUNS_SQL, (cutoff,))
        deleted_pipeline_runs = cursor.rowcount

    return {
        "source_health_events": deleted_source_events,
        "pipeline_runs": deleted_pipeline_runs,
    }


def cleanup_history():
    """使用獨立 transaction 清理過期 history。"""
    retention_days = get_retention_days()
    cutoff = get_retention_cutoff(retention_days)
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        deleted_counts = delete_old_history(connection, cutoff)
        connection.commit()
        return deleted_counts
    except pymysql.MySQLError:
        connection.rollback()
        raise
    finally:
        connection.close()
