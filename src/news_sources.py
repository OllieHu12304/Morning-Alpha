"""集中執行 Morning Alpha 目前啟用的新聞來源。"""

import logging

import requests

from cna_finance_adapter import fetch_articles as fetch_cna_finance
from technews_adapter import fetch_articles as fetch_technews


logger = logging.getLogger(__name__)


def fetch_all_articles_with_status():
    """分開取得各來源，並回傳文章與來源執行結果。"""
    source_fetchers = [
        ("TechNews", fetch_technews),
        ("中央社財經 RSS", fetch_cna_finance),
    ]
    articles = []
    successful_sources = []
    failed_sources = []

    for source_name, fetch_articles in source_fetchers:
        try:
            source_articles = fetch_articles()
        except (requests.RequestException, ValueError) as error:
            logger.error("%s 來源失敗：%s", source_name, error)
            failed_sources.append(source_name)
            continue

        if not source_articles:
            logger.error("%s 來源沒有回傳文章。", source_name)
            failed_sources.append(source_name)
            continue

        articles.extend(source_articles)
        successful_sources.append(source_name)

    if not successful_sources:
        failed_labels = "、".join(failed_sources)
        raise ValueError(f"所有新聞來源都失敗：{failed_labels}。")

    return articles, successful_sources, failed_sources


def fetch_all_articles():
    """依序取得所有來源，合併成共同格式串列。"""
    articles, _, _ = fetch_all_articles_with_status()
    return articles
