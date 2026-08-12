"""測試來源健康卡的時間與來源文字契約。"""

import unittest
from pathlib import Path


DASHBOARD_DIRECTORY = Path(__file__).resolve().parent.parent / "dashboard"


class SourceHealthDashboardContractTests(unittest.TestCase):
    def test_source_health_uses_clear_time_and_yahoo_labels(self):
        javascript = (DASHBOARD_DIRECTORY / "app.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'yahoo_tw_finance: "Yahoo股市聚合 RSS"',
            javascript,
        )
        self.assertIn('"最近擷取"', javascript)
        self.assertIn('"最近成功擷取"', javascript)


if __name__ == "__main__":
    unittest.main()
