"""將 TechNews 首頁文章轉成 Morning Alpha 共同新聞格式。"""

from datetime import datetime

import requests
from bs4 import BeautifulSoup

from news_record import create_news_record


SOURCE = "technews"
NEWS_URL = "https://technews.tw/"
ARTICLE_LIMIT = 5
REQUEST_TIMEOUT = 10
PUBLISH_TIME_FORMAT = "%Y 年 %m 月 %d 日 %H:%M"


def fetch_homepage():
    """下載 TechNews 首頁，並回傳 HTML 文字。"""
    headers = {
        "User-Agent": "MorningAlphaLearningCrawler/0.1"
    }
    response = requests.get(
        NEWS_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def parse_publish_time(publish_time_text):
    """將 TechNews 中文日期文字轉成 datetime。"""
    try:
        return datetime.strptime(
            publish_time_text,
            PUBLISH_TIME_FORMAT,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"無法解析 TechNews 發布時間：{publish_time_text}"
        ) from error


def parse_articles(html):
    """解析 TechNews HTML，並回傳共同格式的最新文章。"""
    soup = BeautifulSoup(html, "html.parser")
    article_elements = soup.select("article.post")
    articles = []

    for article_element in article_elements[:ARTICLE_LIMIT]:
        title_link = article_element.select_one("h1.entry-title a")
        publish_label = None

        for label in article_element.select("span.head"):
            if label.get_text(strip=True) == "發布日期":
                publish_label = label
                break

        if title_link is None or publish_label is None:
            continue

        publish_time_element = publish_label.find_next_sibling(
            "span",
            class_="body",
        )
        url = title_link.get("href")

        if publish_time_element is None or not url:
            continue

        article = create_news_record(
            source=SOURCE,
            source_category=None,
            title=title_link.get_text(strip=True),
            publish_time=parse_publish_time(
                publish_time_element.get_text(strip=True)
            ),
            url=url,
        )
        articles.append(article)

    return articles


def fetch_articles():
    """下載並解析 TechNews，回傳共同格式文章。"""
    return parse_articles(fetch_homepage())


def print_articles(articles):
    """以容易閱讀的格式印出文章資料。"""
    if not articles:
        print("找不到文章，網站結構可能已經改變。")
        return

    for number, article in enumerate(articles, start=1):
        print(f"Article {number}")
        print(f"Source: {article['source']}")
        print(f"Title: {article['title']}")
        print(f"Publish Time: {article['publish_time']}")
        print(f"URL: {article['url']}")
        print("-" * 60)


def main():
    """下載、解析並顯示 TechNews 文章。"""
    try:
        print_articles(fetch_articles())
    except requests.RequestException as error:
        print(f"下載 TechNews 首頁時發生錯誤：{error}")
    except ValueError as error:
        print(f"解析 TechNews 首頁時發生錯誤：{error}")


if __name__ == "__main__":
    main()
