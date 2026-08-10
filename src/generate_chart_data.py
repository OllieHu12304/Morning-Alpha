"""從 dashboard news.json 產生 Chart.js 使用的統計資料。"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"
NEWS_JSON_PATH = DASHBOARD_DIRECTORY / "news.json"
CHART_DATA_PATH = DASHBOARD_DIRECTORY / "chart_data.json"

SOURCE_LABELS = {
    "technews.tw": "TechNews 科技新報",
    "finance.technews.tw": "財經",
    "infosecu.technews.tw": "資訊安全",
    "ccc.technews.tw": "3C",
}

CATEGORY_RULES = {
    "AI 與人工智慧": ["AI", "人工智慧", "ChatGPT", "Claude", "機器學習", "生成式"],
    "半導體": ["半導體", "晶片", "台積電", "聯電", "晶圓", "記憶體", "封裝"],
    "資訊安全": ["資安", "資訊安全", "駭客", "漏洞", "網路攻擊", "詐騙"],
    "財經": ["財報", "營收", "股價", "投資", "金融", "ETF", "利率"],
    "能源": ["能源", "電力", "電池", "太陽能", "風電", "儲能"],
    "交通科技": ["電動車", "汽車", "特斯拉", "Tesla", "無人機"],
    "太空與科學": ["太空", "NASA", "天文", "衛星", "宇宙", "黑洞", "科學"],
}

KEYWORD_CANDIDATES = [
    "AI", "人工智慧", "晶片", "半導體", "台積電",
    "Google", "Apple", "Microsoft", "ChatGPT", "Claude",
    "Tesla", "特斯拉", "資安", "能源", "電池",
    "電動車", "機器人", "衛星", "營收", "投資",
]


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


def infer_category(title):
    """使用標題關鍵字推論一個主要分類。"""
    normalized_title = title.casefold()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword.casefold() in normalized_title:
                return category

    return "其他"


def count_keywords(records):
    """計算每個候選關鍵字出現在多少篇新聞標題中。"""
    keyword_counts = Counter()

    for record in records:
        title = str(record.get("title", "")).casefold()

        for keyword in KEYWORD_CANDIDATES:
            if keyword.casefold() in title:
                keyword_counts[keyword] += 1

    return keyword_counts


def counter_to_chart_data(counter, limit=None):
    """將 Counter 轉成 Chart.js 的 labels 與 values。"""
    items = counter.most_common(limit)

    return {
        "labels": [item[0] for item in items],
        "values": [item[1] for item in items],
    }


def generate_chart_data(records):
    """產生來源、推論分類與 Top 10 keywords 統計。"""
    source_counts = Counter()
    category_counts = Counter()

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("每一筆新聞資料都必須是 object。")

        title = str(record.get("title", ""))
        url = str(record.get("url", ""))
        source_counts[get_source_label(url)] += 1
        category_counts[infer_category(title)] += 1

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
