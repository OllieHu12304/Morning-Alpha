"""集中執行 Morning Alpha 目前啟用的新聞來源。"""

from cna_finance_adapter import fetch_articles as fetch_cna_finance
from technews_adapter import fetch_articles as fetch_technews


def fetch_all_articles():
    """依序取得所有來源，合併成共同格式串列。"""
    articles = []
    articles.extend(fetch_technews())
    articles.extend(fetch_cna_finance())
    return articles
