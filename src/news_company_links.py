"""保存並查詢新聞與公司的規則式比對結果。"""

import pymysql

from company_directory import fetch_company_candidates
from company_matching import (
    build_matching_context,
    match_title_companies_with_context,
)
from store_news import connect_to_database, get_database_config


CREATE_NEWS_COMPANY_LINKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_company_links (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    news_id BIGINT UNSIGNED NOT NULL,
    company_id BIGINT UNSIGNED NOT NULL,
    matched_text VARCHAR(200) NOT NULL,
    match_method VARCHAR(30) NOT NULL,
    confidence DECIMAL(4, 3) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_news_company (news_id, company_id),
    INDEX index_news_company_company (company_id),
    CONSTRAINT foreign_news_company_news
        FOREIGN KEY (news_id) REFERENCES news_records (id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT foreign_news_company_company
        FOREIGN KEY (company_id) REFERENCES companies (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

READ_NEWS_TITLES_SQL = """
SELECT id, title
FROM news_records
ORDER BY id;
"""

DELETE_NEWS_LINKS_SQL = """
DELETE FROM news_company_links
WHERE news_id = %s;
"""

UPSERT_NEWS_COMPANY_LINK_SQL = """
INSERT INTO news_company_links (
    news_id,
    company_id,
    matched_text,
    match_method,
    confidence
)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    matched_text = VALUES(matched_text),
    match_method = VALUES(match_method),
    confidence = VALUES(confidence);
"""

READ_NEWS_COMPANY_LINKS_SQL = """
SELECT
    news_company_links.news_id,
    news_company_links.company_id,
    companies.name,
    companies.short_name,
    industries.name AS industry,
    securities.ticker,
    securities.exchange,
    news_company_links.matched_text,
    news_company_links.match_method,
    news_company_links.confidence
FROM news_company_links
JOIN companies ON companies.id = news_company_links.company_id
LEFT JOIN industries ON industries.id = companies.industry_id
LEFT JOIN securities
    ON securities.company_id = companies.id
    AND securities.is_active = TRUE
"""


def create_news_company_links_table(connection):
    """建立新聞公司關聯表；已存在時直接沿用。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_NEWS_COMPANY_LINKS_TABLE_SQL)


def fetch_news_titles(connection):
    """讀取實體辨識所需的新聞 id 與標題。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_NEWS_TITLES_SQL)
        rows = cursor.fetchall()

    return [
        {"news_id": row[0], "title": row[1]}
        for row in rows
    ]


def replace_news_links(cursor, news_id, matches):
    """以目前辨識結果取代一則新聞的既有關聯。"""
    cursor.execute(DELETE_NEWS_LINKS_SQL, (news_id,))

    for match in matches:
        cursor.execute(
            UPSERT_NEWS_COMPANY_LINK_SQL,
            (
                news_id,
                match["company_id"],
                match["matched_text"],
                match["match_method"],
                match["confidence"],
            ),
        )


def sync_news_company_links(connection):
    """重新分析全部新聞並回傳新聞數與關聯數。"""
    create_news_company_links_table(connection)
    candidates = fetch_company_candidates(connection)
    matching_context = build_matching_context(candidates)
    news_records = fetch_news_titles(connection)
    link_count = 0

    with connection.cursor() as cursor:
        for news_record in news_records:
            matches = match_title_companies_with_context(
                news_record["title"],
                matching_context,
            )
            replace_news_links(
                cursor,
                news_record["news_id"],
                matches,
            )
            link_count += len(matches)

    return {
        "news_count": len(news_records),
        "link_count": link_count,
    }


def run_news_company_sync():
    """使用獨立 transaction 同步新聞公司關聯。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        result = sync_news_company_links(connection)
        connection.commit()
        return result
    except (pymysql.MySQLError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def build_news_company_link_records(rows, column_names):
    """將 MySQL rows 轉成 API 可序列化的 records。"""
    records = []

    for row in rows:
        record = dict(zip(column_names, row))
        record["confidence"] = float(record["confidence"])
        records.append(record)

    return records


def fetch_news_company_links(connection, company_id=None):
    """查詢全部關聯，或只查詢指定公司的關聯。"""
    query = READ_NEWS_COMPANY_LINKS_SQL
    parameters = ()

    if company_id is not None:
        query += " WHERE news_company_links.company_id = %s"
        parameters = (company_id,)

    query += " ORDER BY news_company_links.news_id DESC, companies.id;"

    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return build_news_company_link_records(rows, column_names)


def load_news_company_links(company_id=None):
    """連接 MySQL 並讀取新聞公司關聯。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return fetch_news_company_links(connection, company_id=company_id)
    finally:
        connection.close()
