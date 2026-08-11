"""集中執行 Morning Alpha 目前啟用的新聞來源。"""

import logging

import requests

from cna_finance_adapter import fetch_articles as fetch_cna_finance
from technews_adapter import fetch_articles as fetch_technews
from twse_disclosure_adapter import fetch_articles as fetch_twse_disclosures


logger = logging.getLogger(__name__)


def fetch_all_articles_with_status():
    """分開取得各來源，並回傳文章與來源執行結果。"""
    source_fetchers = [
        ("technews", "TechNews", fetch_technews),
        ("cna", "中央社財經 RSS", fetch_cna_finance),
        (
            "twse_disclosure",
            "TWSE 上市公司每日重大訊息",
            fetch_twse_disclosures,
        ),
    ]
    articles = []
    source_results = []

    for source, source_name, fetch_articles in source_fetchers:
        try:
            source_articles = fetch_articles()
        except (requests.RequestException, ValueError) as error:
            logger.error("%s 來源失敗：%s", source_name, error)
            source_results.append({
                "source": source,
                "source_name": source_name,
                "status": "failure",
                "article_count": 0,
                "error_message": str(error),
            })
            continue

        if not source_articles:
            logger.error("%s 來源沒有回傳文章。", source_name)
            source_results.append({
                "source": source,
                "source_name": source_name,
                "status": "failure",
                "article_count": 0,
                "error_message": "來源沒有回傳文章。",
            })
            continue

        articles.extend(source_articles)
        source_results.append({
            "source": source,
            "source_name": source_name,
            "status": "success",
            "article_count": len(source_articles),
            "error_message": None,
        })

    return articles, source_results


def fetch_all_articles():
    """依序取得所有來源，合併成共同格式串列。"""
    articles, source_results = fetch_all_articles_with_status()

    if not articles:
        failed_labels = "、".join(
            result["source_name"] for result in source_results
        )
        raise ValueError(f"所有新聞來源都失敗：{failed_labels}。")

    return articles
