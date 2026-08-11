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

    def test_dashboard_loads_news_and_analytics_api(self):
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")

        self.assertIn('const NEWS_API = "/api/news"', javascript)
        self.assertIn('const ANALYTICS_API = "/api/analytics"', javascript)
        self.assertNotIn('const NEWS_FILE = "./news.json"', javascript)
        self.assertNotIn('const KEYWORD_FILE = "./keyword.json"', javascript)
        self.assertIn("keywordRecordsToSeries", javascript)
        self.assertIn("formatLastUpdated", javascript)

    def test_dashboard_can_filter_related_events(self):
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn("event_group_id", javascript)
        self.assertIn("eventGroupFilter", javascript)
        self.assertIn("查看同事件", javascript)
        self.assertIn("source_category", javascript)
        self.assertIn(".event-filter-button", styles)


if __name__ == "__main__":
    unittest.main()
