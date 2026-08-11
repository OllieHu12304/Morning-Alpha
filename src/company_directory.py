"""建立 Morning Alpha 的公司、產業與股票代號資料表。"""

import pymysql

from store_news import connect_to_database, get_database_config


CREATE_INDUSTRIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS industries (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_industry_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

CREATE_COMPANIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    short_name VARCHAR(100) NULL,
    industry_id BIGINT UNSIGNED NULL,
    market VARCHAR(30) NOT NULL DEFAULT 'TWSE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_company_market_name (market, name),
    CONSTRAINT foreign_company_industry
        FOREIGN KEY (industry_id) REFERENCES industries (id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

CREATE_SECURITIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS securities (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id BIGINT UNSIGNED NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    exchange VARCHAR(30) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'TWD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_security_exchange_ticker (exchange, ticker),
    INDEX index_security_company (company_id),
    CONSTRAINT foreign_security_company
        FOREIGN KEY (company_id) REFERENCES companies (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

CREATE_COMPANY_ALIASES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS company_aliases (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_id BIGINT UNSIGNED NOT NULL,
    alias VARCHAR(200) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_company_alias (company_id, alias),
    INDEX index_company_alias_text (alias),
    CONSTRAINT foreign_alias_company
        FOREIGN KEY (company_id) REFERENCES companies (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

COMPANY_DIRECTORY_TABLE_STATEMENTS = [
    CREATE_INDUSTRIES_TABLE_SQL,
    CREATE_COMPANIES_TABLE_SQL,
    CREATE_SECURITIES_TABLE_SQL,
    CREATE_COMPANY_ALIASES_TABLE_SQL,
]

UPSERT_INDUSTRY_SQL = """
INSERT INTO industries (name)
VALUES (%s)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
"""

UPSERT_COMPANY_SQL = """
INSERT INTO companies (name, short_name, industry_id, market)
VALUES (%s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    id = LAST_INSERT_ID(id),
    short_name = VALUES(short_name),
    industry_id = VALUES(industry_id);
"""

UPSERT_SECURITY_SQL = """
INSERT INTO securities (company_id, ticker, exchange, currency, is_active)
VALUES (%s, %s, %s, %s, TRUE)
ON DUPLICATE KEY UPDATE
    company_id = VALUES(company_id),
    currency = VALUES(currency),
    is_active = TRUE;
"""

INSERT_ALIAS_SQL = """
INSERT IGNORE INTO company_aliases (company_id, alias)
VALUES (%s, %s);
"""

READ_COMPANY_CANDIDATES_SQL = """
SELECT
    companies.id AS company_id,
    companies.name,
    companies.short_name,
    industries.name AS industry,
    securities.ticker,
    securities.exchange,
    company_aliases.alias
FROM companies
JOIN securities ON securities.company_id = companies.id
LEFT JOIN industries ON industries.id = companies.industry_id
LEFT JOIN company_aliases ON company_aliases.company_id = companies.id
WHERE securities.is_active = TRUE
ORDER BY companies.id, securities.id, company_aliases.id;
"""


def create_company_directory_tables(connection):
    """按照 foreign key 相依順序建立四張公司資料表。"""
    with connection.cursor() as cursor:
        for statement in COMPANY_DIRECTORY_TABLE_STATEMENTS:
            cursor.execute(statement)


def ensure_company_directory():
    """以獨立 transaction 建立公司資料模型。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_company_directory_tables(connection)
        connection.commit()
    except pymysql.MySQLError:
        connection.rollback()
        raise
    finally:
        connection.close()


def validate_company_record(record):
    """確認 adapter 提供公司匯入需要的共同欄位。"""
    required_fields = [
        "name",
        "short_name",
        "industry",
        "market",
        "ticker",
        "exchange",
        "currency",
    ]

    if not isinstance(record, dict):
        raise ValueError("公司紀錄必須是 object。")

    if any(not str(record.get(field, "")).strip() for field in required_fields):
        raise ValueError("公司紀錄缺少必要欄位。")

    aliases = record.get("aliases")

    if not isinstance(aliases, list) or not aliases:
        raise ValueError("公司紀錄必須包含至少一個 alias。")


def upsert_company_record(cursor, record):
    """以同一 cursor 更新一筆公司、股票與別名資料。"""
    validate_company_record(record)
    cursor.execute(UPSERT_INDUSTRY_SQL, (record["industry"],))
    industry_id = cursor.lastrowid
    cursor.execute(
        UPSERT_COMPANY_SQL,
        (
            record["name"],
            record["short_name"],
            industry_id,
            record["market"],
        ),
    )
    company_id = cursor.lastrowid
    cursor.execute(
        UPSERT_SECURITY_SQL,
        (
            company_id,
            record["ticker"],
            record["exchange"],
            record["currency"],
        ),
    )

    for alias in record["aliases"]:
        cleaned_alias = str(alias).strip()

        if cleaned_alias:
            cursor.execute(
                INSERT_ALIAS_SQL,
                (company_id, cleaned_alias),
            )


def import_company_records(connection, records):
    """匯入共同格式公司資料並回傳處理筆數。"""
    if not isinstance(records, list):
        raise ValueError("records 必須是 list。")

    create_company_directory_tables(connection)

    with connection.cursor() as cursor:
        for record in records:
            upsert_company_record(cursor, record)

    return len(records)


def sync_company_records(records):
    """使用獨立 transaction 匯入公司資料。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        imported_count = import_company_records(connection, records)
        connection.commit()
        return imported_count
    except (pymysql.MySQLError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def build_company_candidates(rows, column_names):
    """將 MySQL join rows 合併成一公司／股票一筆的候選資料。"""
    candidates_by_key = {}

    for row in rows:
        record = dict(zip(column_names, row))
        key = (
            record["company_id"],
            record["exchange"],
            record["ticker"],
        )

        if key not in candidates_by_key:
            candidates_by_key[key] = {
                "company_id": record["company_id"],
                "name": record["name"],
                "short_name": record["short_name"],
                "industry": record["industry"],
                "ticker": record["ticker"],
                "exchange": record["exchange"],
                "aliases": [],
            }

        alias = record.get("alias")

        if alias and alias not in candidates_by_key[key]["aliases"]:
            candidates_by_key[key]["aliases"].append(alias)

    return list(candidates_by_key.values())


def fetch_company_candidates(connection):
    """讀取實體辨識需要的公司候選資料。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_COMPANY_CANDIDATES_SQL)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return build_company_candidates(rows, column_names)


def load_company_candidates():
    """連接 MySQL 並讀取公司候選資料。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return fetch_company_candidates(connection)
    finally:
        connection.close()
