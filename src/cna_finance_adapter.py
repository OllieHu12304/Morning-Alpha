"""將中央社財經 RSS 轉成 Morning Alpha 共同新聞格式。"""

from email.utils import parsedate_to_datetime
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

import requests

from news_record import create_news_record


SOURCE = "cna"
SOURCE_CATEGORY = "產經證券"
RSS_URL = "https://feeds.feedburner.com/rsscna/finance"
REQUEST_TIMEOUT = 10
TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")


def fetch_feed():
    """下載中央社財經 RSS，並回傳 XML 文字。"""
    headers = {
        "User-Agent": "MorningAlphaLearningCrawler/0.1"
    }
    response = requests.get(
        RSS_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def parse_publish_time(publish_time_text):
    """將 RSS 日期轉成台北時間的 datetime。"""
    try:
        publish_time = parsedate_to_datetime(publish_time_text)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"無法解析中央社 RSS 發布時間：{publish_time_text}"
        ) from error

    if publish_time.tzinfo is not None:
        publish_time = publish_time.astimezone(TAIPEI_TIMEZONE)
        publish_time = publish_time.replace(tzinfo=None)

    return publish_time


def parse_articles(xml_text):
    """解析 RSS XML，並回傳共同格式的全部文章。"""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as error:
        raise ValueError("中央社 RSS XML 格式無法解析。") from error

    articles = []

    for item in root.findall("./channel/item"):
        title = item.findtext("title")
        url = item.findtext("link")
        publish_time_text = item.findtext("pubDate")

        if not title or not url or not publish_time_text:
            continue

        article = create_news_record(
            source=SOURCE,
            source_category=SOURCE_CATEGORY,
            title=title,
            publish_time=parse_publish_time(publish_time_text),
            url=url,
        )
        articles.append(article)

    return articles


def fetch_articles():
    """下載並解析中央社財經 RSS。"""
    return parse_articles(fetch_feed())


if __name__ == "__main__":
    for news_article in fetch_articles():
        print(news_article)
