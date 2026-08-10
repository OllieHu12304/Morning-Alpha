"""測試 Feature 7 的圖表統計資料產生邏輯。"""

import json
import tempfile
import unittest
from pathlib import Path

from src.generate_chart_data import (
    export_chart_data,
    generate_chart_data,
    get_source_label,
    infer_category,
)


class GenerateChartDataTests(unittest.TestCase):
    def test_get_source_label_maps_known_hostname(self):
        self.assertEqual(
            get_source_label("https://finance.technews.tw/2026/08/10/example"),
            "財經",
        )

    def test_infer_category_is_case_insensitive(self):
        self.assertEqual(infer_category("Claude 推出生成式 AI 新功能"), "AI 與人工智慧")

    def test_generate_chart_data_counts_each_dimension(self):
        records = [
            {
                "title": "台積電 AI 晶片投資增加",
                "url": "https://technews.tw/example-1",
            },
            {
                "title": "資安漏洞引發網路攻擊",
                "url": "https://infosecu.technews.tw/example-2",
            },
            {
                "title": "Apple 發表新產品",
                "url": "https://example.com/example-3",
            },
        ]

        chart_data = generate_chart_data(records)

        self.assertEqual(chart_data["sources"]["values"], [1, 1, 1])
        self.assertEqual(chart_data["categories"]["labels"], [
            "AI 與人工智慧",
            "資訊安全",
            "其他",
        ])
        self.assertEqual(chart_data["keywords"]["labels"][:3], [
            "AI",
            "晶片",
            "台積電",
        ])

    def test_generate_chart_data_rejects_non_object_record(self):
        with self.assertRaisesRegex(ValueError, "object"):
            generate_chart_data(["invalid record"])

    def test_export_chart_data_writes_utf8_json(self):
        chart_data = {
            "sources": {"labels": ["科技新報"], "values": [2]},
            "categories": {"labels": ["半導體"], "values": [2]},
            "keywords": {"labels": ["台積電"], "values": [2]},
        }

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "chart_data.json"
            export_chart_data(chart_data, output_path)

            with output_path.open(encoding="utf-8") as json_file:
                self.assertEqual(json.load(json_file), chart_data)


if __name__ == "__main__":
    unittest.main()
