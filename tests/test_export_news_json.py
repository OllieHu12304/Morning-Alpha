"""測試 Dashboard 新聞與 metadata JSON 的準備流程。"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from export_news_json import (  # noqa: E402
    build_metadata,
    export_metadata,
    prepare_dashboard_records,
)


class ExportNewsJsonTests(unittest.TestCase):
    def test_prepare_dashboard_records_includes_news_dimensions(self):
        dataframe = pd.DataFrame([{
            "source": "cna",
            "source_category": "產經證券",
            "analysis_category": "半導體",
            "title": "測試新聞",
            "publish_time": datetime(2026, 8, 11, 9, 30),
            "url": "https://www.cna.com.tw/news/example.aspx",
        }])

        records = prepare_dashboard_records(dataframe)

        self.assertEqual(records, [{
            "source": "cna",
            "source_category": "產經證券",
            "analysis_category": "半導體",
            "title": "測試新聞",
            "publish_time": "2026-08-11T09:30:00",
            "url": "https://www.cna.com.tw/news/example.aspx",
        }])

    def test_prepare_dashboard_records_exports_null_categories(self):
        dataframe = pd.DataFrame([{
            "source": "technews",
            "source_category": None,
            "analysis_category": None,
            "title": "測試新聞",
            "publish_time": datetime(2026, 8, 11, 9, 30),
            "url": "https://technews.tw/example/",
        }])

        record = prepare_dashboard_records(dataframe)[0]

        self.assertIsNone(record["source_category"])
        self.assertIsNone(record["analysis_category"])

    def test_prepare_dashboard_records_can_include_internal_id(self):
        dataframe = pd.DataFrame([{
            "id": 7,
            "source": "technews",
            "source_category": None,
            "analysis_category": "半導體",
            "title": "測試新聞",
            "publish_time": datetime(2026, 8, 11, 9, 30),
            "url": "https://technews.tw/example/",
        }])

        record = prepare_dashboard_records(dataframe, include_id=True)[0]

        self.assertEqual(record["id"], 7)

    def test_build_metadata_requires_and_preserves_timezone(self):
        taipei_timezone = timezone(timedelta(hours=8))
        updated_at = datetime(2026, 8, 11, 14, 30, tzinfo=taipei_timezone)

        metadata = build_metadata(updated_at)

        self.assertEqual(
            metadata,
            {"last_updated": "2026-08-11T14:30:00+08:00"},
        )

        with self.assertRaisesRegex(ValueError, "timezone"):
            build_metadata(datetime(2026, 8, 11, 14, 30))

    def test_export_metadata_writes_utf8_json(self):
        metadata = {"last_updated": "2026-08-11T14:30:00+08:00"}

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "metadata.json"
            export_metadata(metadata, output_path)

            with output_path.open(encoding="utf-8") as json_file:
                self.assertEqual(json.load(json_file), metadata)


if __name__ == "__main__":
    unittest.main()
