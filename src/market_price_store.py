"""將 TWSE 每日價格保存到 MySQL。"""

from datetime import timezone

import pymysql

from store_news import connect_to_database, get_database_config


CREATE_MARKET_PRICES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS market_prices (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    security_id BIGINT UNSIGNED NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(18, 4) NULL,
    high_price DECIMAL(18, 4) NULL,
    low_price DECIMAL(18, 4) NULL,
    close_price DECIMAL(18, 4) NULL,
    price_change DECIMAL(18, 4) NULL,
    volume BIGINT UNSIGNED NULL,
    trade_value DECIMAL(24, 2) NULL,
    transaction_count BIGINT UNSIGNED NULL,
    source VARCHAR(100) NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_security_trade_date (security_id, trade_date),
    INDEX index_market_price_trade_date (trade_date),
    CONSTRAINT foreign_market_price_security
        FOREIGN KEY (security_id) REFERENCES securities (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

READ_SECURITIES_SQL = """
SELECT id, exchange, ticker
FROM securities
WHERE is_active = TRUE;
"""

UPSERT_MARKET_PRICE_SQL = """
INSERT INTO market_prices (
    security_id,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    price_change,
    volume,
    trade_value,
    transaction_count,
    source,
    fetched_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    open_price = VALUES(open_price),
    high_price = VALUES(high_price),
    low_price = VALUES(low_price),
    close_price = VALUES(close_price),
    price_change = VALUES(price_change),
    volume = VALUES(volume),
    trade_value = VALUES(trade_value),
    transaction_count = VALUES(transaction_count),
    source = VALUES(source),
    fetched_at = VALUES(fetched_at);
"""


def create_market_prices_table(connection):
    """建立每日價格資料表。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_MARKET_PRICES_TABLE_SQL)


def fetch_security_ids(connection):
    """以 exchange 與 ticker 建立 security id 對照表。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_SECURITIES_SQL)
        rows = cursor.fetchall()

    return {
        (row[1], row[2]): row[0]
        for row in rows
    }


def prepare_market_price_rows(records, security_ids):
    """將共同格式轉成 PyMySQL rows，並計算未對應證券。"""
    rows = []
    skipped_count = 0

    for record in records:
        security_id = security_ids.get((record["exchange"], record["ticker"]))

        if security_id is None:
            skipped_count += 1
            continue

        fetched_at = record["fetched_at"]

        if fetched_at.tzinfo is None:
            raise ValueError("市場價格 fetched_at 必須包含 timezone。")

        fetched_at_utc = fetched_at.astimezone(timezone.utc).replace(tzinfo=None)
        rows.append((
            security_id,
            record["trade_date"],
            record["open_price"],
            record["high_price"],
            record["low_price"],
            record["close_price"],
            record["price_change"],
            record["volume"],
            record["trade_value"],
            record["transaction_count"],
            record["source"],
            fetched_at_utc,
        ))

    return rows, skipped_count


def upsert_market_prices(connection, records):
    """保存已能對應 securities 的價格並回傳同步摘要。"""
    if not isinstance(records, list) or not records:
        raise ValueError("市場價格 records 必須是非空 list。")

    create_market_prices_table(connection)
    security_ids = fetch_security_ids(connection)
    rows, skipped_count = prepare_market_price_rows(records, security_ids)

    if rows:
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_MARKET_PRICE_SQL, rows)

    return {
        "source_count": len(records),
        "saved_count": len(rows),
        "skipped_count": skipped_count,
    }


def save_market_prices(records):
    """使用獨立 transaction 保存每日價格。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        result = upsert_market_prices(connection, records)
        connection.commit()
        return result
    except (pymysql.MySQLError, KeyError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()
