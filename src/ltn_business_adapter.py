"""將自由時報財經 RSS 轉成 Morning Alpha 共同新聞格式。"""

from email.utils import parsedate_to_datetime
import logging
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from http_client import fetch_text
from news_record import create_news_record


SOURCE = "ltn"
SOURCE_CATEGORY = "財經"
SOURCE_NAME = "自由時報財經 RSS"
RSS_URL = "https://news.ltn.com.tw/rss/business.xml"
REQUEST_TIMEOUT = 10
TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")

logger = logging.getLogger(__name__)


def fetch_feed():
    """下載自由時報財經 RSS，並回傳 XML 文字。"""
    headers = {
        "User-Agent": "MorningAlphaLearningCrawler/0.1",
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
            f"無法解析自由時報 RSS 發布時間：{publish_time_text}"
        ) from error

    if publish_time.tzinfo is not None:
        publish_time = publish_time.astimezone(TAIPEI_TIMEZONE)
        publish_time = publish_time.replace(tzinfo=None)

    return publish_time


def parse_articles(xml_text):
    """解析 RSS XML，略過缺少必要欄位的 item。"""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as error:
        raise ValueError("自由時報 RSS XML 格式無法解析。") from error

    item_elements = root.findall("./channel/item")

    if not item_elements:
        raise ValueError("自由時報 RSS 結構異常：找不到 item。")

    articles = []
    skipped_count = 0

    for item in item_elements:
        title = item.findtext("title")
        url = item.findtext("link")
        publish_time_text = item.findtext("pubDate")

        if not title or not url or not publish_time_text:
            skipped_count += 1
            continue

        articles.append(create_news_record(
            source=SOURCE,
            source_category=SOURCE_CATEGORY,
            title=title,
            publish_time=parse_publish_time(publish_time_text),
            url=url,
        ))

    if skipped_count:
        logger.warning(
            "自由時報 RSS 有 %s 筆 item 缺少必要欄位。",
            skipped_count,
        )

    if not articles:
        raise ValueError("自由時報 RSS 結構異常：沒有可用文章。")

    return articles


def fetch_articles():
    """下載並解析自由時報財經 RSS。"""
    return parse_articles(fetch_feed())


if __name__ == "__main__":
    for news_article in fetch_articles():
        print(news_article)
