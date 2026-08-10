"""使用 Pandas 分析新聞標題中的 Top 20 關鍵字。"""

import json
import re
from pathlib import Path

import pandas as pd


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"
NEWS_JSON_PATH = DASHBOARD_DIRECTORY / "news.json"
KEYWORD_JSON_PATH = DASHBOARD_DIRECTORY / "keyword.json"
TOP_KEYWORD_LIMIT = 20

# 中文標題不能只靠空白可靠斷詞，因此先使用可維護的科技與投資關鍵字詞庫。
KEYWORD_CANDIDATES = [
    "AI",
    "人工智慧",
    "生成式 AI",
    "ChatGPT",
    "Claude",
    "Gemini",
    "OpenAI",
    "Google",
    "Apple",
    "Microsoft",
    "Meta",
    "NVIDIA",
    "輝達",
    "晶片",
    "半導體",
    "台積電",
    "聯電",
    "晶圓",
    "記憶體",
    "封裝",
    "資安",
    "駭客",
    "漏洞",
    "雲端",
    "資料中心",
    "機器人",
    "能源",
    "電池",
    "太陽能",
    "電動車",
    "Tesla",
    "特斯拉",
    "衛星",
    "太空",
    "營收",
    "財報",
    "股價",
    "投資",
    "ETF",
    "利率",
]


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
    candidates=KEYWORD_CANDIDATES,
    limit=TOP_KEYWORD_LIMIT,
):
    """統計每個候選字詞在標題中的總出現次數，回傳前 limit 名。"""
    if limit < 1:
        raise ValueError("limit 必須大於 0。")

    if "title" not in dataframe.columns or dataframe.empty:
        return pd.DataFrame(columns=["keyword", "count"])

    normalized_titles = (
        dataframe["title"]
        .fillna("")
        .astype("string")
        .str.casefold()
    )

    keyword_counts = pd.Series(
        {
            keyword: int(
                normalized_titles.str.count(
                    re.escape(keyword.casefold()),
                ).sum()
            )
            for keyword in candidates
        },
        dtype="int64",
        name="count",
    )

    result = (
        keyword_counts[keyword_counts > 0]
        .rename_axis("keyword")
        .reset_index()
        .sort_values(
            by=["count", "keyword"],
            ascending=[False, True],
            kind="stable",
        )
        .head(limit)
        .reset_index(drop=True)
    )

    return result


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
