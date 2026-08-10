"""將 MySQL 新聞匯出成 HTML dashboard 使用的 JSON 檔案。"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import pymysql

from read_news import load_all_news


JSON_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "dashboard" / "news.json"
)
METADATA_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "dashboard" / "metadata.json"
)


def prepare_dashboard_records(dataframe):
    """將完整 DataFrame 整理成可匯出的新聞字典串列。"""
    if dataframe.empty:
        return []

    dataframe = dataframe.copy()
    dataframe["publish_time"] = pd.to_datetime(
        dataframe["publish_time"],
        errors="coerce",
    )
    dataframe = dataframe.sort_values(
        by="publish_time",
        ascending=False,
    )

    records = []

    for _, row in dataframe.iterrows():
        publish_time = row["publish_time"]

        if pd.isna(publish_time):
            publish_time_text = None
        else:
            publish_time_text = publish_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

        record = {
            "source": row["source"],
            "source_category": optional_text(row["source_category"]),
            "analysis_category": optional_text(row["analysis_category"]),
            "title": row["title"],
            "publish_time": publish_time_text,
            "url": row["url"],
        }
        records.append(record)

    return records


def optional_text(value):
    """將 MySQL NULL 或 Pandas NaN 轉成 JSON null。"""
    if pd.isna(value):
        return None

    return str(value)


def build_metadata(updated_at=None):
    """建立 Dashboard 資料更新時間。"""
    if updated_at is None:
        updated_at = datetime.now().astimezone()

    if updated_at.tzinfo is None:
        raise ValueError("Dashboard 更新時間必須包含 timezone。")

    return {
        "last_updated": updated_at.isoformat(timespec="seconds"),
    }


def export_json(records, output_path=JSON_OUTPUT_PATH):
    """將新聞串列寫入 UTF-8 JSON 檔案。"""
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(
            records,
            json_file,
            ensure_ascii=False,
            indent=2,
        )


def export_metadata(metadata, output_path=METADATA_OUTPUT_PATH):
    """將 Dashboard metadata 寫入 UTF-8 JSON。"""
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(
            metadata,
            json_file,
            ensure_ascii=False,
            indent=2,
        )


def main():
    """從 MySQL 讀取全部新聞並匯出 dashboard JSON。"""
    try:
        dataframe = load_all_news()
        records = prepare_dashboard_records(dataframe)
        export_json(records)
        export_metadata(build_metadata())
        print(f"成功匯出 {len(records)} 筆新聞到 {JSON_OUTPUT_PATH}。")
    except pymysql.MySQLError as error:
        print(f"讀取 MySQL 時發生錯誤：{error}")
    except ValueError as error:
        print(f"MySQL 設定錯誤：{error}")
    except OSError as error:
        print(f"寫入 JSON 時發生錯誤：{error}")


if __name__ == "__main__":
    main()
