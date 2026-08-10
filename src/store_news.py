"""將整理完成的 TechNews 新聞寫入 MySQL。"""

import os

import pandas as pd
import pymysql
import requests

from analyze_news import create_dataframe, transform_dataframe
from canonical_url_hash import create_canonical_url_hash
from news_category import infer_category
from news_sources import fetch_all_articles
from url_normalizer import normalize_url

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    source_category VARCHAR(100) NULL,
    analysis_category VARCHAR(100) NULL,
    title VARCHAR(500) NOT NULL,
    publish_time DATETIME NOT NULL,
    url VARCHAR(1000) NOT NULL,
    canonical_url VARCHAR(1000) NOT NULL,
    canonical_url_hash CHAR(64)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_canonical_url_hash (canonical_url_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

INSERT_NEWS_SQL = """
INSERT IGNORE INTO news_records (
    source,
    source_category,
    analysis_category,
    title,
    publish_time,
    url,
    canonical_url,
    canonical_url_hash
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""


def get_database_config():
    """從環境變數取得 MySQL 連線設定。"""
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")

    if not user or not password:
        raise ValueError(
            "請先設定 MYSQL_USER 與 MYSQL_PASSWORD 環境變數。"
        )

    try:
        port = int(os.getenv("MYSQL_PORT", "3306"))
    except ValueError as error:
        raise ValueError("MYSQL_PORT 必須是整數。") from error

    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": port,
        "user": user,
        "password": password,
        "database": os.getenv("MYSQL_DATABASE", "morning_alpha"),
    }


def connect_to_database(config):
    """使用 PyMySQL 建立資料庫連線。"""
    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset="utf8mb4",
        autocommit=False,
    )


def create_news_table(connection):
    """建立 news_records table；已存在時不重複建立。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_TABLE_SQL)


def prepare_news_records(dataframe):
    """將 DataFrame 每一列轉成 PyMySQL 可以插入的 tuple。"""
    records = []

    for _, row in dataframe.iterrows():
        source = row["source"]
        source_category = row["source_category"]
        title = row["title"]
        publish_time = row["publish_time"]
        url = row["url"]

        if pd.isna(title) or pd.isna(url) or not title or not url:
            raise ValueError("新聞資料包含空白欄位，無法寫入 MySQL。")

        if pd.isna(publish_time):
            raise ValueError("新聞發布時間無法轉換，無法寫入 MySQL。")

        canonical_url = normalize_url(url)

        record = (
            source,
            source_category,
            infer_category(title),
            title,
            publish_time.to_pydatetime(),
            url,
            canonical_url,
            create_canonical_url_hash(canonical_url),
        )
        records.append(record)

    return records


def insert_news_records(connection, dataframe):
    """將 DataFrame 中的新聞資料插入 news_records table。"""
    records = prepare_news_records(dataframe)

    if not records:
        return 0

    with connection.cursor() as cursor:
        inserted_count = cursor.executemany(INSERT_NEWS_SQL, records)

    return inserted_count


def save_news(dataframe):
    """建立 table，插入新聞，並管理 transaction 與連線。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_news_table(connection)
        inserted_count = insert_news_records(connection, dataframe)
        connection.commit()
        return inserted_count
    except (pymysql.MySQLError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def main():
    """取得、整理並寫入目前所有來源的新聞。"""
    try:
        articles = fetch_all_articles()
        dataframe = create_dataframe(articles)
        dataframe = transform_dataframe(dataframe)
        inserted_count = save_news(dataframe)
        print(f"成功寫入 {inserted_count} 筆新聞資料。")
    except requests.RequestException as error:
        print(f"下載新聞來源時發生錯誤：{error}")
    except pymysql.MySQLError as error:
        print(f"寫入 MySQL 時發生錯誤：{error}")
    except ValueError as error:
        print(f"設定或資料錯誤：{error}")


if __name__ == "__main__":
    main()
