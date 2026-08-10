"""從 dashboard news.json 產生 Chart.js 使用的統計資料。"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from analyze_keywords import (
    KEYWORD_CANDIDATES,
    count_top_keywords,
    create_title_dataframe,
)
from news_category import infer_category


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"
NEWS_JSON_PATH = DASHBOARD_DIRECTORY / "news.json"
CHART_DATA_PATH = DASHBOARD_DIRECTORY / "chart_data.json"

SOURCE_LABELS = {
    "technews.tw": "TechNews 科技新報",
    "finance.technews.tw": "財經",
    "infosecu.technews.tw": "資訊安全",
    "ccc.technews.tw": "3C",
}
SOURCE_CODE_LABELS = {
    "cna": "中央通訊社",
    "technews": "TechNews 科技新報",
}

def load_news_records(input_path=NEWS_JSON_PATH):
    """讀取 Feature 6 匯出的新聞 JSON。"""
    with input_path.open("r", encoding="utf-8") as json_file:
        records = json.load(json_file)

    if not isinstance(records, list):
        raise ValueError("news.json 最外層必須是 list。")

    return records


def get_source_label(url):
    """從新聞 URL hostname 推導來源名稱。"""
    hostname = urlparse(url).hostname

    if not hostname:
        return "未知來源"

    hostname = hostname.removeprefix("www.")
    return SOURCE_LABELS.get(hostname, hostname)


def get_record_source_label(record):
    """優先使用正式 source 欄位，舊資料才由 URL 推導。"""
    source = record.get("source")

    if source:
        return SOURCE_CODE_LABELS.get(source, str(source))

    return get_source_label(str(record.get("url", "")))


def count_keywords(records):
    """使用 Top 20 相同的 Pandas 規則計算全部候選詞。"""
    dataframe = create_title_dataframe(records)
    keyword_dataframe = count_top_keywords(
        dataframe,
        candidates=KEYWORD_CANDIDATES,
        limit=len(KEYWORD_CANDIDATES),
    )

    return Counter(dict(zip(
        keyword_dataframe["keyword"],
        keyword_dataframe["count"],
    )))


def counter_to_chart_data(counter, limit=None):
    """將 Counter 轉成 Chart.js 的 labels 與 values。"""
    items = counter.most_common(limit)

    return {
        "labels": [item[0] for item in items],
        "values": [item[1] for item in items],
    }


def generate_chart_data(records):
    """產生來源、推論分類與統一規則的 Top 10 統計。"""
    source_counts = Counter()
    category_counts = Counter()

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("每一筆新聞資料都必須是 object。")

        title = str(record.get("title", ""))
        source_counts[get_record_source_label(record)] += 1
        category = record.get("analysis_category") or infer_category(title)
        category_counts[category] += 1

    keyword_counts = count_keywords(records)

    return {
        "sources": counter_to_chart_data(source_counts),
        "categories": counter_to_chart_data(category_counts),
        "keywords": counter_to_chart_data(keyword_counts, limit=10),
    }


def export_chart_data(chart_data, output_path=CHART_DATA_PATH):
    """將統計結果寫入 UTF-8 JSON。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(chart_data, json_file, ensure_ascii=False, indent=2)


def main():
    """讀取新聞、產生統計，並匯出 dashboard chart data。"""
    try:
        records = load_news_records()
        chart_data = generate_chart_data(records)
        export_chart_data(chart_data)
        print(f"成功產生圖表資料：{CHART_DATA_PATH}")
    except json.JSONDecodeError as error:
        print(f"news.json 格式錯誤：{error}")
    except ValueError as error:
        print(f"新聞資料錯誤：{error}")
    except OSError as error:
        print(f"讀寫 JSON 時發生錯誤：{error}")


if __name__ == "__main__":
    main()
