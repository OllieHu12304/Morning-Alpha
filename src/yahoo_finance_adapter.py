"""將 Yahoo股市台股動態 RSS 轉成 Morning Alpha 共同新聞格式。"""

from email.utils import parsedate_to_datetime
import logging
import re
from pathlib import PurePosixPath
from urllib.parse import urlparse
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from http_client import fetch_text
from news_record import create_news_record


SOURCE = "yahoo_tw_finance"
SOURCE_CATEGORY = "台股動態"
SOURCE_NAME = "Yahoo股市台股動態 RSS"
DEFAULT_PUBLISHER = "Yahoo股市"
RSS_URL = "https://tw.stock.yahoo.com/rss?category=tw-market"
REQUEST_TIMEOUT = 10
TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")

logger = logging.getLogger(__name__)


def extract_article_id(value):
    """從 Yahoo 新聞網址末尾取得九位數文章 ID。"""
    if not value:
        return None

    path_stem = PurePosixPath(urlparse(value.strip()).path).stem
    match = re.search(r"(\d{9})$", path_stem)

    if match:
        return match.group(1)

    return None


def get_source_article_id(guid, url):
    """優先使用 RSS guid，必要時改從文章網址取得 ID。"""
    guid = (guid or "").strip()

    if guid:
        guid_article_id = extract_article_id(guid)
        return guid_article_id or guid

    return extract_article_id(url)


def get_publisher(item):
    """讀取 RSS source；正式 feed 未提供時明確標記為 Yahoo股市。"""
    source_element = item.findtext("source")

    if source_element and source_element.strip():
        return source_element.strip()

    return DEFAULT_PUBLISHER


def fetch_feed():
    """下載 Yahoo股市官方 RSS，並回傳 XML 文字。"""
    headers = {
        "User-Agent": "MorningAlphaLearningCrawler/0.1",
        "Accept": "application/rss+xml, application/xml, text/xml",
    }
    return fetch_text(
        RSS_URL,
        source_name=SOURCE_NAME,
        timeout=REQUEST_TIMEOUT,
        headers=headers,
    )


def parse_publish_time(publish_time_text):
    """將 RSS 日期轉成不含時區資訊的台北時間。"""
    try:
        publish_time = parsedate_to_datetime(publish_time_text)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"無法解析 Yahoo股市 RSS 發布時間：{publish_time_text}"
        ) from error

    if publish_time.tzinfo is not None:
        publish_time = publish_time.astimezone(TAIPEI_TIMEZONE)
        publish_time = publish_time.replace(tzinfo=None)

    return publish_time


def parse_articles(xml_text):
    """解析 Yahoo RSS，並保留聚合管道、可得 publisher 與文章 ID。"""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as error:
        raise ValueError("Yahoo股市 RSS XML 格式無法解析。") from error

    item_elements = root.findall("./channel/item")

    if not item_elements:
        raise ValueError("Yahoo股市 RSS 結構異常：找不到 item。")

    articles = []
    skipped_count = 0

    for item in item_elements:
        title = item.findtext("title")
        url = item.findtext("link")
        publish_time_text = item.findtext("pubDate")
        guid = item.findtext("guid")

        if not title or not url or not publish_time_text:
            skipped_count += 1
            continue

        publisher = get_publisher(item)
        source_article_id = get_source_article_id(guid, url)

        if not source_article_id:
            skipped_count += 1
            continue

        articles.append(create_news_record(
            source=SOURCE,
            publisher=publisher,
            source_article_id=source_article_id,
            source_category=SOURCE_CATEGORY,
            title=title,
            publish_time=parse_publish_time(publish_time_text),
            url=url,
        ))

    if skipped_count:
        logger.warning(
            "Yahoo股市 RSS 有 %s 筆 item 缺少必要欄位或文章 ID。",
            skipped_count,
        )

    if not articles:
        raise ValueError("Yahoo股市 RSS 結構異常：沒有可用文章。")

    return articles


def fetch_articles():
    """下載並解析 Yahoo股市台股動態 RSS。"""
    return parse_articles(fetch_feed())


if __name__ == "__main__":
    for news_article in fetch_articles():
        print(news_article)
