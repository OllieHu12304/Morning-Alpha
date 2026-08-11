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
