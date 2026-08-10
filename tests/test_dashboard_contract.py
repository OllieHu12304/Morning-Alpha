"""測試 Dashboard 與 Python 輸出檔案的基本契約。"""

import unittest
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
DASHBOARD_DIRECTORY = PROJECT_DIRECTORY / "dashboard"


class DashboardContractTests(unittest.TestCase):
    def test_dashboard_contains_filter_and_pagination_controls(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")

        for element_id in [
            "news-search",
            "source-filter",
            "category-filter",
            "page-size",
            "previous-page",
            "next-page",
        ]:
            self.assertIn(f'id="{element_id}"', html)

    def test_dashboard_loads_keyword_and_metadata_json(self):
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")

        self.assertIn('const KEYWORD_FILE = "./keyword.json"', javascript)
        self.assertIn('const METADATA_FILE = "./metadata.json"', javascript)
        self.assertIn("keywordRecordsToSeries", javascript)
        self.assertIn("formatLastUpdated", javascript)


if __name__ == "__main__":
    unittest.main()
