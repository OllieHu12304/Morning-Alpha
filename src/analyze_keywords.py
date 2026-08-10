"""使用 Pandas 分析新聞標題中的 Top 20 關鍵字。"""

import json
import logging
from pathlib import Path

import jieba
import pandas as pd


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"
NEWS_JSON_PATH = DASHBOARD_DIRECTORY / "news.json"
KEYWORD_JSON_PATH = DASHBOARD_DIRECTORY / "keyword.json"
USER_DICTIONARY_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "jieba_user_dictionary.txt"
)
TOP_KEYWORD_LIMIT = 20

MIN_KEYWORD_LENGTH = 2
STOP_WORDS = {
    "一個",
    "以及",
    "今年",
    "今天",
    "使用",
    "可能",
    "成為",
    "我們",
    "推出",
    "新聞",
    "最新",
    "沒有",
    "目前",
    "相關",
    "表示",
    "進行",
}

jieba.setLogLevel(logging.WARNING)
jieba.load_userdict(str(USER_DICTIONARY_PATH))


def load_news_dataframe(input_path=NEWS_JSON_PATH):
    """讀取 news.json 並建立只包含 title 欄位的 DataFrame。"""
    with input_path.open("r", encoding="utf-8") as json_file:
        records = json.load(json_file)

    return create_title_dataframe(records)


def create_title_dataframe(records):
    """將新聞 dict 串列轉成只包含 title 的 DataFrame。"""
    if not isinstance(records, list):
        raise ValueError("news.json 最外層必須是 list。")

    if any(not isinstance(record, dict) for record in records):
        raise ValueError("每一筆新聞資料都必須是 object。")

    dataframe = pd.DataFrame.from_records(records)

    if "title" not in dataframe.columns:
        return pd.DataFrame({"title": pd.Series(dtype="string")})

    return dataframe.loc[:, ["title"]]


def count_top_keywords(
    dataframe,
    limit=TOP_KEYWORD_LIMIT,
):
    """使用 jieba 斷詞與 Pandas 統計熱門關鍵字。"""
    if limit is not None and limit < 1:
        raise ValueError("limit 必須大於 0。")

    if "title" not in dataframe.columns or dataframe.empty:
        return pd.DataFrame(columns=["keyword", "count"])

    token_rows = []

    for title in dataframe["title"].fillna("").astype("string"):
        for token in extract_keywords(title):
            token_rows.append({
                "normalized_keyword": token.casefold(),
                "keyword": token,
            })

    if not token_rows:
        return pd.DataFrame(columns=["keyword", "count"])

    token_dataframe = pd.DataFrame(token_rows)
    result = (
        token_dataframe
        .groupby("normalized_keyword", as_index=False, sort=False)
        .agg(
            keyword=("keyword", "first"),
            count=("keyword", "size"),
        )
        .loc[:, ["keyword", "count"]]
        .sort_values(
            by=["count", "keyword"],
            ascending=[False, True],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    if limit is not None:
        result = result.head(limit).reset_index(drop=True)

    return result


def extract_keywords(title):
    """將一個標題切成適合統計的資訊詞。"""
    keywords = []

    for token in jieba.lcut(str(title), cut_all=False):
        token = token.strip()

        if len(token) < MIN_KEYWORD_LENGTH:
            continue

        if token.casefold() in STOP_WORDS:
            continue

        if token.replace(".", "", 1).isdigit():
            continue

        if not any(character.isalnum() for character in token):
            continue

        keywords.append(token)

    return keywords


def export_keyword_json(dataframe, output_path=KEYWORD_JSON_PATH):
    """將關鍵字 DataFrame 匯出成 UTF-8 JSON array。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = dataframe.to_dict(orient="records")

    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=2)


def main():
    """讀取新聞、計算 Top 20 關鍵字並匯出 keyword.json。"""
    try:
        dataframe = load_news_dataframe()
        keyword_dataframe = count_top_keywords(dataframe)
        export_keyword_json(keyword_dataframe)
        print(
            f"成功匯出 {len(keyword_dataframe)} 個關鍵字到 "
            f"{KEYWORD_JSON_PATH}。"
        )
    except json.JSONDecodeError as error:
        print(f"news.json 格式錯誤：{error}")
    except ValueError as error:
        print(f"新聞資料錯誤：{error}")
    except OSError as error:
        print(f"讀寫 JSON 時發生錯誤：{error}")


if __name__ == "__main__":
    main()
