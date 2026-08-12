"""建立新聞發布時間與公司收盤價變化的保守觀察。"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from store_news import connect_to_database, get_database_config


MARKET_CLOSE_TIME = time(13, 30)
DEFAULT_OBSERVATION_LIMIT = 20
MAX_OBSERVATION_LIMIT = 100
MAX_EVENT_CANDIDATES = 1000

ANALYSIS_TYPE = "observational"
METHODOLOGY = (
    "收盤前發布使用當日或下一個交易日收盤；"
    "收盤後發布使用下一個交易日收盤，並與前一交易日比較。"
)
LIMITATIONS = [
    "此結果只描述時間相近的價格變化，不代表新聞造成價格變動。",
    "每日收盤價無法反映盤中反應、其他新聞或整體市場因素。",
    "資料不足時不產生觀察，也不以零或推測值補齊。",
]

READ_EVENT_CANDIDATES_SQL = """
SELECT
    news_records.title,
    news_records.publish_time,
    news_records.url,
    news_records.source,
    companies.id AS company_id,
    companies.name AS company_name,
    companies.short_name,
    securities.id AS security_id,
    securities.ticker,
    securities.exchange,
    news_company_links.confidence AS match_confidence
FROM news_company_links
JOIN news_records ON news_records.id = news_company_links.news_id
JOIN companies ON companies.id = news_company_links.company_id
JOIN securities ON securities.company_id = companies.id
WHERE securities.is_active = TRUE
ORDER BY news_records.publish_time DESC
LIMIT %s;
"""

READ_SECURITY_PRICES_SQL = """
SELECT trade_date, close_price
FROM market_prices
WHERE security_id = %s
    AND close_price IS NOT NULL
ORDER BY trade_date DESC
LIMIT 365;
"""

READ_EVENT_READINESS_SQL = """
SELECT
    (SELECT COUNT(*) FROM news_company_links) AS candidate_count,
    (SELECT COUNT(DISTINCT trade_date) FROM market_prices) AS price_date_count,
    (SELECT MIN(trade_date) FROM market_prices) AS earliest_trade_date,
    (SELECT MAX(trade_date) FROM market_prices) AS latest_trade_date;
"""


def validate_observation_limit(limit):
    """限制單次分析筆數，避免無界線查詢。"""
    if (
        not isinstance(limit, int)
        or limit < 1
        or limit > MAX_OBSERVATION_LIMIT
    ):
        raise ValueError("觀察筆數 limit 必須是 1 到 100 的整數。")


def rows_to_records(rows, column_names):
    """將 MySQL rows 轉成 dictionaries。"""
    return [
        dict(zip(column_names, row))
        for row in rows
    ]


def fetch_event_candidates(connection, limit):
    """讀取最近且已匹配公司的新聞。"""
    if (
        not isinstance(limit, int)
        or limit < 1
        or limit > MAX_EVENT_CANDIDATES
    ):
        raise ValueError("候選新聞 limit 必須是 1 到 1000 的整數。")

    with connection.cursor() as cursor:
        cursor.execute(READ_EVENT_CANDIDATES_SQL, (limit,))
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return rows_to_records(rows, column_names)


def fetch_security_prices(connection, security_id):
    """讀取一檔證券所有可使用的每日收盤價。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_SECURITY_PRICES_SQL, (security_id,))
        rows = cursor.fetchall()

    return [
        {"trade_date": row[0], "close_price": row[1]}
        for row in rows
    ]


def fetch_event_market_readiness(connection):
    """回報事件觀察所需的公司關聯與價格日期涵蓋狀態。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_EVENT_READINESS_SQL)
        row = cursor.fetchone()

    return {
        "candidate_count": int(row[0]),
        "price_date_count": int(row[1]),
        "earliest_trade_date": row[2].isoformat() if row[2] else None,
        "latest_trade_date": row[3].isoformat() if row[3] else None,
    }


def parse_publish_time(value):
    """接受 MySQL datetime 或 ISO 文字。"""
    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError("新聞發布時間格式不正確。") from error


def get_target_date(publish_time):
    """依台灣市場 13:30 收盤界線取得最早觀察日期。"""
    if publish_time.time() < MARKET_CLOSE_TIME:
        return publish_time.date()

    return publish_time.date() + timedelta(days=1)


def select_observation_window(publish_time, prices):
    """選出觀察收盤日與其前一個有價格的交易日。"""
    target_date = get_target_date(parse_publish_time(publish_time))
    sorted_prices = sorted(
        prices,
        key=lambda record: record["trade_date"],
    )
    observation_index = None

    for index, price_record in enumerate(sorted_prices):
        if price_record["trade_date"] >= target_date:
            observation_index = index
            break

    if observation_index is None or observation_index == 0:
        return None

    return (
        sorted_prices[observation_index - 1],
        sorted_prices[observation_index],
    )


def calculate_change(baseline_close, observation_close):
    """以 Decimal 計算價差與百分比，再轉成 API 數字。"""
    baseline = Decimal(str(baseline_close))
    observation = Decimal(str(observation_close))

    if baseline <= 0:
        raise ValueError("基準收盤價必須大於零。")

    price_change = observation - baseline
    change_percent = (price_change / baseline) * Decimal("100")
    return float(price_change), float(round(change_percent, 4))


def build_event_market_observation(candidate, prices):
    """為一則公司新聞建立一筆時間關聯觀察。"""
    window = select_observation_window(candidate["publish_time"], prices)

    if window is None:
        return None

    baseline_price, observation_price = window
    price_change, change_percent = calculate_change(
        baseline_price["close_price"],
        observation_price["close_price"],
    )
    publish_time = parse_publish_time(candidate["publish_time"])

    return {
        "title": candidate["title"],
        "url": candidate["url"],
        "source": candidate["source"],
        "publish_time": publish_time.isoformat(timespec="seconds"),
        "company_id": candidate["company_id"],
        "company_name": candidate["company_name"],
        "short_name": candidate.get("short_name"),
        "ticker": candidate["ticker"],
        "exchange": candidate["exchange"],
        "match_confidence": float(candidate["match_confidence"]),
        "baseline_trade_date": baseline_price["trade_date"].isoformat(),
        "baseline_close": float(baseline_price["close_price"]),
        "observation_trade_date": (
            observation_price["trade_date"].isoformat()
        ),
        "observation_close": float(observation_price["close_price"]),
        "price_change": price_change,
        "change_percent": change_percent,
        "analysis_type": ANALYSIS_TYPE,
    }


def create_event_market_observations(connection, limit=DEFAULT_OBSERVATION_LIMIT):
    """建立最近可計算的觀察，並快取同一證券的價格。"""
    validate_observation_limit(limit)
    candidate_limit = min(limit * 20, MAX_EVENT_CANDIDATES)
    candidates = fetch_event_candidates(connection, candidate_limit)
    prices_by_security = {}
    observations = []

    for candidate in candidates:
        security_id = candidate["security_id"]

        if security_id not in prices_by_security:
            prices_by_security[security_id] = fetch_security_prices(
                connection,
                security_id,
            )

        observation = build_event_market_observation(
            candidate,
            prices_by_security[security_id],
        )

        if observation is not None:
            observations.append(observation)

        if len(observations) == limit:
            break

    return observations


def load_event_market_observations(limit=DEFAULT_OBSERVATION_LIMIT):
    """連接 MySQL 並建立事件市場觀察。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return create_event_market_observations(connection, limit=limit)
    finally:
        connection.close()


def load_event_market_analysis(limit=DEFAULT_OBSERVATION_LIMIT):
    """以同一連線回傳觀察結果與資料就緒狀態。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        observations = create_event_market_observations(
            connection,
            limit=limit,
        )
        readiness = fetch_event_market_readiness(connection)
        readiness["observation_count"] = len(observations)
        return observations, readiness
    finally:
        connection.close()
