"""測試 Feature 8 的 Pandas 關鍵字分析流程。"""

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analyze_keywords import (
    count_top_keywords,
    create_title_dataframe,
    export_keyword_json,
    load_news_dataframe,
)


class AnalyzeKeywordsTests(unittest.TestCase):
    def test_create_title_dataframe_rejects_non_object_record(self):
        with self.assertRaisesRegex(ValueError, "object"):
            create_title_dataframe(["invalid record"])

    def test_count_top_keywords_counts_mentions_case_insensitively(self):
        dataframe = pd.DataFrame({
            "title": [
                "AI 晶片帶動投資，AI 應用持續增加",
                "ai 伺服器推升晶片需求",
            ],
        })

        result = count_top_keywords(
            dataframe,
            candidates=["AI", "晶片", "投資"],
        )

        self.assertEqual(result.to_dict(orient="records"), [
            {"keyword": "AI", "count": 3},
            {"keyword": "晶片", "count": 2},
            {"keyword": "投資", "count": 1},
        ])

    def test_count_top_keywords_applies_limit(self):
        dataframe = pd.DataFrame({"title": ["AI 晶片 投資"]})

        result = count_top_keywords(
            dataframe,
            candidates=["AI", "晶片", "投資"],
            limit=2,
        )

        self.assertEqual(len(result), 2)

    def test_count_top_keywords_defaults_to_top_twenty(self):
        candidates = [f"keyword-{index:02d}" for index in range(25)]
        dataframe = pd.DataFrame({"title": [" ".join(candidates)]})

        result = count_top_keywords(dataframe, candidates=candidates)

        self.assertEqual(len(result), 20)

    def test_count_top_keywords_ignores_missing_titles(self):
        dataframe = pd.DataFrame({"title": [None, "", "AI"]})

        result = count_top_keywords(dataframe, candidates=["AI"])

        self.assertEqual(result.to_dict(orient="records"), [
            {"keyword": "AI", "count": 1},
        ])

    def test_load_news_dataframe_rejects_non_list_json(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "news.json"
            input_path.write_text('{"title": "AI"}', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "list"):
                load_news_dataframe(input_path)

    def test_export_keyword_json_writes_records(self):
        dataframe = pd.DataFrame([
            {"keyword": "半導體", "count": 4},
            {"keyword": "AI", "count": 3},
        ])

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "keyword.json"
            export_keyword_json(dataframe, output_path)

            with output_path.open(encoding="utf-8") as json_file:
                self.assertEqual(json.load(json_file), [
                    {"keyword": "半導體", "count": 4},
                    {"keyword": "AI", "count": 3},
                ])


if __name__ == "__main__":
    unittest.main()
