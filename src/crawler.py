"""取得並顯示 TechNews 首頁最新五篇文章。"""

import requests
from bs4 import BeautifulSoup


NEWS_URL = "https://technews.tw/"
ARTICLE_LIMIT = 5
REQUEST_TIMEOUT = 10


def fetch_homepage():
    """下載 TechNews 首頁，並回傳網頁的 HTML 文字。"""
    headers = {
        "User-Agent": "MorningAlphaLearningCrawler/0.1"
    }

    response = requests.get(
        NEWS_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    # 如果網站回傳 4xx 或 5xx 狀態碼，這一行會產生錯誤。
    response.raise_for_status()

    return response.text


def parse_articles(html):
    """從首頁 HTML 中整理最新五篇文章。"""
    soup = BeautifulSoup(html, "html.parser")
    article_elements = soup.select("article.post")
    articles = []

    for article_element in article_elements[:ARTICLE_LIMIT]:
        title_link = article_element.select_one("h1.entry-title a")
        publish_label = None

        # 同一篇文章有數個 span.head，逐一尋找「發布日期」。
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

        if publish_time_element is None:
            continue

        article = {
            "title": title_link.get_text(strip=True),
            "publish_time": publish_time_element.get_text(strip=True),
            "url": title_link.get("href"),
        }
        articles.append(article)

    return articles


def print_articles(articles):
    """以容易閱讀的格式印出文章資料。"""
    if not articles:
        print("找不到文章，網站結構可能已經改變。")
        return

    for number, article in enumerate(articles, start=1):
        print(f"Article {number}")
        print(f"Title: {article['title']}")
        print(f"Publish Time: {article['publish_time']}")
        print(f"URL: {article['url']}")
        print("-" * 60)


def main():
    """依序執行下載、解析與顯示。"""
    try:
        html = fetch_homepage()
        articles = parse_articles(html)
        print_articles(articles)
    except requests.RequestException as error:
        print(f"下載 TechNews 首頁時發生錯誤：{error}")


if __name__ == "__main__":
    main()
