"""將 TechNews 爬蟲結果整理成 Pandas DataFrame。"""

import pandas as pd
import requests

from crawler import fetch_homepage, parse_articles


PUBLISH_TIME_FORMAT = "%Y 年 %m 月 %d 日 %H:%M"


def create_dataframe(articles):
    """將文章串列轉換成 DataFrame。"""
    return pd.DataFrame(articles)


def transform_dataframe(dataframe):
    """轉換時間格式並依發布時間排序。"""
    if dataframe.empty:
        return dataframe

    # 將文字時間轉為 Pandas 可以排序與分析的 datetime。
    dataframe["publish_time"] = pd.to_datetime(
        dataframe["publish_time"],
        format=PUBLISH_TIME_FORMAT,
        errors="coerce",
    )

    # ascending=False 代表依時間由新到舊排列。
    dataframe = dataframe.sort_values(
        by="publish_time",
        ascending=False,
    )

    # 排序後重新建立從 0 開始的連續索引。
    dataframe = dataframe.reset_index(drop=True)

    return dataframe


def print_dataframe(dataframe):
    """印出完整 DataFrame，不顯示索引欄位。"""
    if dataframe.empty:
        print("沒有可顯示的新聞資料。")
        return

    print(dataframe.to_string(index=False))


def main():
    """取得新聞、建立 DataFrame、轉換資料並印出結果。"""
    try:
        html = fetch_homepage()
        articles = parse_articles(html)
        dataframe = create_dataframe(articles)
        dataframe = transform_dataframe(dataframe)
        print_dataframe(dataframe)
    except requests.RequestException as error:
        print(f"下載 TechNews 首頁時發生錯誤：{error}")


if __name__ == "__main__":
    main()
