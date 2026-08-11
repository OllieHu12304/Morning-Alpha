"""將 TWSE 季度財務摘要保存到 MySQL。"""

from datetime import timezone

import pymysql

from store_news import connect_to_database, get_database_config


CREATE_FINANCIAL_METRICS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS financial_metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    security_id BIGINT UNSIGNED NOT NULL,
    report_date DATE NOT NULL,
    fiscal_year SMALLINT UNSIGNED NOT NULL,
    fiscal_quarter TINYINT UNSIGNED NOT NULL,
    industry VARCHAR(100) NULL,
    earnings_per_share DECIMAL(20, 4) NULL,
    face_value_text VARCHAR(100) NULL,
    operating_revenue DECIMAL(30, 2) NULL,
    operating_income DECIMAL(30, 2) NULL,
    non_operating_income_expense DECIMAL(30, 2) NULL,
    net_income DECIMAL(30, 2) NULL,
    currency CHAR(3) NOT NULL DEFAULT 'TWD',
    source VARCHAR(100) NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_security_fiscal_period (
        security_id,
        fiscal_year,
        fiscal_quarter
    ),
    INDEX index_financial_report_date (report_date),
    CONSTRAINT foreign_financial_metric_security
        FOREIGN KEY (security_id) REFERENCES securities (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

READ_SECURITIES_SQL = """
SELECT id, exchange, ticker
FROM securities
WHERE is_active = TRUE;
"""

UPSERT_FINANCIAL_METRIC_SQL = """
INSERT INTO financial_metrics (
    security_id,
    report_date,
    fiscal_year,
    fiscal_quarter,
    industry,
    earnings_per_share,
    face_value_text,
    operating_revenue,
    operating_income,
    non_operating_income_expense,
    net_income,
    currency,
    source,
    fetched_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    report_date = VALUES(report_date),
    industry = VALUES(industry),
    earnings_per_share = VALUES(earnings_per_share),
    face_value_text = VALUES(face_value_text),
    operating_revenue = VALUES(operating_revenue),
    operating_income = VALUES(operating_income),
    non_operating_income_expense = VALUES(non_operating_income_expense),
    net_income = VALUES(net_income),
    currency = VALUES(currency),
    source = VALUES(source),
    fetched_at = VALUES(fetched_at);
"""


def create_financial_metrics_table(connection):
    """建立季度財務摘要資料表。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_FINANCIAL_METRICS_TABLE_SQL)


def fetch_security_ids(connection):
    """建立 exchange 與 ticker 對 security id 的 mapping。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_SECURITIES_SQL)
        rows = cursor.fetchall()

    return {
        (row[1], row[2]): row[0]
        for row in rows
    }


def prepare_financial_metric_rows(records, security_ids):
    """將財務共同格式轉成 PyMySQL rows。"""
    rows = []
    skipped_count = 0

    for record in records:
        security_id = security_ids.get((record["exchange"], record["ticker"]))

        if security_id is None:
            skipped_count += 1
            continue

        fetched_at = record["fetched_at"]

        if fetched_at.tzinfo is None:
            raise ValueError("財務資料 fetched_at 必須包含 timezone。")

        fetched_at_utc = fetched_at.astimezone(timezone.utc).replace(tzinfo=None)
        rows.append((
            security_id,
            record["report_date"],
            record["fiscal_year"],
            record["fiscal_quarter"],
            record["industry"],
            record["earnings_per_share"],
            record["face_value_text"],
            record["operating_revenue"],
            record["operating_income"],
            record["non_operating_income_expense"],
            record["net_income"],
            record["currency"],
            record["source"],
            fetched_at_utc,
        ))

    return rows, skipped_count


def upsert_financial_metrics(connection, records):
    """保存已能對應 securities 的財務摘要並回傳計數。"""
    if not isinstance(records, list) or not records:
        raise ValueError("財務資料 records 必須是非空 list。")

    create_financial_metrics_table(connection)
    security_ids = fetch_security_ids(connection)
    rows, skipped_count = prepare_financial_metric_rows(
        records,
        security_ids,
    )

    if rows:
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_FINANCIAL_METRIC_SQL, rows)

    return {
        "source_count": len(records),
        "saved_count": len(rows),
        "skipped_count": skipped_count,
    }


def save_financial_metrics(records):
    """使用獨立 transaction 保存季度財務摘要。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        result = upsert_financial_metrics(connection, records)
        connection.commit()
        return result
    except (pymysql.MySQLError, KeyError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()
