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
            "company-filter",
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

    def test_dashboard_loads_and_renders_source_health(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="source-health-grid"', html)
        self.assertIn('const SOURCE_HEALTH_API = "/api/source-health"', javascript)
        self.assertIn("renderSourceHealth", javascript)
        self.assertIn("createSourceHealthCard", javascript)
        self.assertIn(".source-health-badge-success", styles)
        self.assertIn(".source-health-badge-failure", styles)

    def test_dashboard_loads_and_renders_pipeline_history(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="pipeline-runs-list"', html)
        self.assertIn('const PIPELINE_RUNS_API = "/api/pipeline-runs"', javascript)
        self.assertIn("renderPipelineRuns", javascript)
        self.assertIn("createPipelineStepItem", javascript)
        self.assertIn(".pipeline-run-badge-success", styles)
        self.assertIn(".pipeline-run-badge-failure", styles)

    def test_dashboard_loads_and_renders_daily_brief(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="daily-brief-content"', html)
        self.assertIn(
            'const LATEST_DAILY_BRIEF_API = "/api/daily-briefs/latest"',
            javascript,
        )
        self.assertIn("renderDailyBrief", javascript)
        self.assertIn("createBriefHighlight", javascript)
        self.assertIn(".daily-brief-content", styles)

    def test_dashboard_can_filter_related_events(self):
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn("event_group_id", javascript)
        self.assertIn("eventGroupFilter", javascript)
        self.assertIn("查看同事件", javascript)
        self.assertIn("source_category", javascript)
        self.assertIn(".event-filter-button", styles)

    def test_dashboard_displays_and_filters_related_companies(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="company-filter"', html)
        self.assertIn("populateCompanyFilter", javascript)
        self.assertIn("getCompanyLabel", javascript)
        self.assertIn("company.company_id", javascript)
        self.assertIn(".company-tag", styles)

    def test_dashboard_displays_company_market_and_financial_data(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="market-company-select"', html)
        self.assertIn('id="company-price-chart"', html)
        self.assertIn('id="company-financial-body"', html)
        self.assertIn('const MARKET_COMPANIES_API = "/api/market-companies"', javascript)
        self.assertIn("loadSelectedCompanyMarketData", javascript)
        self.assertIn("renderCompanyPriceChart", javascript)
        self.assertIn("renderFinancialTable", javascript)
        self.assertIn("不構成投資建議", html)
        self.assertIn(".company-market-content", styles)

    def test_dashboard_labels_event_market_analysis_as_non_causal(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="event-market-body"', html)
        self.assertIn("時間關聯，非因果", html)
        self.assertIn("不構成投資建議", html)
        self.assertIn('const EVENT_MARKET_API = "/api/event-market-observations"', javascript)
        self.assertIn("renderEventMarketObservations", javascript)
        self.assertIn('observation.analysis_type !== "observational"', javascript)
        self.assertIn(".observation-badge", styles)

    def test_dashboard_manages_watchlist_and_personalized_brief(self):
        html = (DASHBOARD_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(encoding="utf-8")
        styles = (DASHBOARD_DIRECTORY / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="watchlist-toggle"', html)
        self.assertIn('id="watchlist-company-search"', html)
        self.assertIn('id="watchlist-search-results"', html)
        self.assertIn('id="personalized-brief-result"', html)
        self.assertIn('const WATCHLIST_API = "/api/watchlist"', javascript)
        self.assertIn(
            'const PERSONALIZED_BRIEF_API = "/api/personalized-brief"',
            javascript,
        )
        self.assertIn("toggleSelectedCompanyWatchlist", javascript)
        self.assertIn("renderWatchlistSearchResults", javascript)
        self.assertIn("setWatchlistCompany", javascript)
        self.assertIn("renderPersonalizedBrief", javascript)
        self.assertIn("![4, 9].includes(record.step_results.length)", javascript)
        self.assertIn(".watchlist-items", styles)
        self.assertIn(".watchlist-search-results", styles)
        self.assertIn(".watchlist-remove-button", styles)
        self.assertIn(
            'twse_disclosure: "TWSE 官方重大訊息"',
            javascript,
        )


if __name__ == "__main__":
    unittest.main()
