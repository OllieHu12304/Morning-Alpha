"""保存本機單一使用者的公司追蹤清單。"""

import pymysql

from store_news import connect_to_database, get_database_config


CREATE_WATCHLIST_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS watchlist_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_watchlist_company (company_id),
    CONSTRAINT foreign_watchlist_company
        FOREIGN KEY (company_id) REFERENCES companies (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

COMPANY_EXISTS_SQL = """
SELECT id
FROM companies
WHERE id = %s;
"""

INSERT_WATCHLIST_ITEM_SQL = """
INSERT IGNORE INTO watchlist_items (company_id)
VALUES (%s);
"""

DELETE_WATCHLIST_ITEM_SQL = """
DELETE FROM watchlist_items
WHERE company_id = %s;
"""

READ_WATCHLIST_SQL = """
SELECT
    watchlist_items.id,
    watchlist_items.company_id,
    companies.name,
    companies.short_name,
    industries.name AS industry,
    securities.ticker,
    securities.exchange,
    watchlist_items.created_at
FROM watchlist_items
JOIN companies ON companies.id = watchlist_items.company_id
LEFT JOIN industries ON industries.id = companies.industry_id
LEFT JOIN securities ON securities.id = (
    SELECT MIN(active_security.id)
    FROM securities AS active_security
    WHERE active_security.company_id = companies.id
        AND active_security.is_active = TRUE
)
ORDER BY watchlist_items.created_at, watchlist_items.id;
"""


def validate_company_id(company_id):
    """拒絕布林值、文字與非正整數 company id。"""
    if isinstance(company_id, bool) or not isinstance(company_id, int):
        raise ValueError("company_id 必須是正整數。")

    if company_id <= 0:
        raise ValueError("company_id 必須是正整數。")


def create_watchlist_table(connection):
    """建立追蹤清單 table；已存在時不重複建立。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_WATCHLIST_TABLE_SQL)


def ensure_watchlist_table():
    """以獨立 transaction 確保 Dashboard 第一次使用前已有 table。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_watchlist_table(connection)
        connection.commit()
    except pymysql.MySQLError:
        connection.rollback()
        raise
    finally:
        connection.close()


def insert_watchlist_item(connection, company_id):
    """加入一家公司；不存在的公司會回報清楚的資料錯誤。"""
    validate_company_id(company_id)

    with connection.cursor() as cursor:
        cursor.execute(COMPANY_EXISTS_SQL, (company_id,))

        if cursor.fetchone() is None:
            raise ValueError("找不到指定公司。")

        cursor.execute(INSERT_WATCHLIST_ITEM_SQL, (company_id,))
        return cursor.rowcount == 1


def delete_watchlist_item(connection, company_id):
    """移除一家公司，並回傳是否真的刪除一筆資料。"""
    validate_company_id(company_id)

    with connection.cursor() as cursor:
        cursor.execute(DELETE_WATCHLIST_ITEM_SQL, (company_id,))
        return cursor.rowcount == 1


def build_watchlist_records(rows, column_names):
    """將 MySQL rows 轉成 API 可序列化的追蹤公司。"""
    records = []

    for row in rows:
        record = dict(zip(column_names, row))
        created_at = record.get("created_at")

        if hasattr(created_at, "isoformat"):
            record["created_at"] = created_at.isoformat(timespec="seconds")

        records.append(record)

    return records


def fetch_watchlist(connection):
    """依加入順序讀取追蹤公司。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_WATCHLIST_SQL)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return build_watchlist_records(rows, column_names)


def load_watchlist():
    """連接 MySQL 並讀取完整追蹤清單。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return fetch_watchlist(connection)
    finally:
        connection.close()


def add_watchlist_company(company_id):
    """用獨立 transaction 加入追蹤公司。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_watchlist_table(connection)
        added = insert_watchlist_item(connection, company_id)
        connection.commit()
        return added
    except (pymysql.MySQLError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def remove_watchlist_company(company_id):
    """用獨立 transaction 移除追蹤公司。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        removed = delete_watchlist_item(connection, company_id)
        connection.commit()
        return removed
    except (pymysql.MySQLError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()
