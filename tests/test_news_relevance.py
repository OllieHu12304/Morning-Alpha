"""測試新聞相關性規則與既有 MySQL 資料顯示過濾。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from news_relevance import is_relevant_news  # noqa: E402
from read_news import create_news_dataframe  # noqa: E402


class NewsRelevanceTests(unittest.TestCase):
    def test_cna_lottery_titles_are_not_relevant(self):
        for title in [
            "今彩539第115193期 頭獎1注中獎",
            "威力彩第115064期 頭獎槓龜",
            "大樂透本期開獎結果",
        ]:
            with self.subTest(title=title):
                self.assertFalse(is_relevant_news("cna", title))

    def test_finance_title_and_other_sources_remain_relevant(self):
        self.assertTrue(is_relevant_news("cna", "台股收盤上漲"))
        self.assertTrue(is_relevant_news("technews", "彩券系統技術更新"))

    def test_old_cna_lottery_record_is_hidden_from_dataframe(self):
        columns = ["id", "source", "title"]
        rows = [
            (1, "cna", "威力彩第115064期 頭獎槓龜"),
            (2, "cna", "台股收盤上漲"),
            (3, "technews", "人工智慧新聞"),
        ]

        dataframe = create_news_dataframe(rows, columns)

        self.assertEqual(dataframe["id"].tolist(), [2, 3])


if __name__ == "__main__":
    unittest.main()
