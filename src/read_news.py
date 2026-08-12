"""從 MySQL 讀取新聞，並顯示發布時間最新的 20 筆。"""

import pandas as pd
import pymysql

from news_relevance import is_relevant_news
from store_news import connect_to_database, get_database_config


READ_ALL_NEWS_SQL = """
SELECT
    id,
    source,
    publisher,
    source_article_id,
    source_category,
    analysis_category,
    title,
    publish_time,
    url,
    created_at
FROM news_records;
"""

DISPLAY_LIMIT = 20
DASHBOARD_SOURCE_LIMIT = 60


def fetch_all_news(connection):
    """從 news_records 讀取全部資料與欄位名稱。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_ALL_NEWS_SQL)
        rows = cursor.fetchall()

        # cursor.description 保存 SELECT 結果的欄位資訊。
        column_names = []
        for column in cursor.description:
            column_names.append(column[0])

    return rows, column_names


def create_news_dataframe(rows, column_names):
    """建立 DataFrame，並隱藏已確認不符合專案目標的舊資料。"""
    dataframe = pd.DataFrame(rows, columns=column_names)

    if dataframe.empty:
        return dataframe

    relevant_rows = dataframe.apply(
        lambda row: is_relevant_news(row["source"], row["title"]),
        axis=1,
    )
    return dataframe.loc[relevant_rows].reset_index(drop=True)


def get_latest_news(dataframe):
    """按照發布時間由新到舊排列，並保留最新 20 筆。"""
    if dataframe.empty:
        return dataframe

    # 使用副本，避免排序顯示時改變原本的完整 DataFrame。
    dataframe = dataframe.copy()

    dataframe["publish_time"] = pd.to_datetime(
        dataframe["publish_time"],
        errors="coerce",
    )

    latest_news = dataframe.sort_values(
        by="publish_time",
        ascending=False,
    ).head(DISPLAY_LIMIT)

    return latest_news.reset_index(drop=True)


def get_balanced_recent_news(
    dataframe,
    per_source_limit=DASHBOARD_SOURCE_LIMIT,
):
    """每個取得來源保留發布時間最新的固定筆數，再合併排序。"""
    if (
        not isinstance(per_source_limit, int)
        or isinstance(per_source_limit, bool)
        or per_source_limit < 1
    ):
        raise ValueError("每個來源的新聞上限必須是正整數。")

    if dataframe.empty:
        return dataframe.copy()

    required_columns = {"source", "publish_time"}

    if not required_columns.issubset(dataframe.columns):
        raise ValueError("平衡新聞資料需要 source 與 publish_time 欄位。")

    prepared_dataframe = dataframe.copy()
    prepared_dataframe["publish_time"] = pd.to_datetime(
        prepared_dataframe["publish_time"],
        errors="coerce",
    )
    source_dataframes = []

    for source in prepared_dataframe["source"].dropna().unique():
        source_dataframe = prepared_dataframe.loc[
            prepared_dataframe["source"] == source
        ]
        source_dataframe = source_dataframe.sort_values(
            by="publish_time",
            ascending=False,
        ).head(per_source_limit)
        source_dataframes.append(source_dataframe)

    if not source_dataframes:
        return prepared_dataframe.iloc[0:0].copy()

    balanced_dataframe = pd.concat(
        source_dataframes,
        ignore_index=True,
    )
    balanced_dataframe = balanced_dataframe.sort_values(
        by="publish_time",
        ascending=False,
    )
    return balanced_dataframe.reset_index(drop=True)


def load_all_news():
    """連接 MySQL、讀取全部新聞、建立 DataFrame 並關閉連線。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        rows, column_names = fetch_all_news(connection)
        return create_news_dataframe(rows, column_names)
    finally:
        connection.close()


def print_latest_news(dataframe):
    """印出最新 20 筆新聞，不顯示 DataFrame 索引。"""
    if dataframe.empty:
        print("news_records 目前沒有新聞資料。")
        return

    print(dataframe.to_string(index=False))


def main():
    """讀取所有新聞，並印出發布時間最新的 20 筆。"""
    try:
        dataframe = load_all_news()
        latest_news = get_latest_news(dataframe)
        print_latest_news(latest_news)
    except pymysql.MySQLError as error:
        print(f"讀取 MySQL 時發生錯誤：{error}")
    except ValueError as error:
        print(f"MySQL 設定錯誤：{error}")


if __name__ == "__main__":
    main()
