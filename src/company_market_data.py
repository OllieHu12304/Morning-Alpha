"""查詢 Dashboard 使用的公司價格與財務摘要。"""

from datetime import date, datetime
from decimal import Decimal

from store_news import connect_to_database, get_database_config


READ_MARKET_COMPANIES_SQL = """
SELECT
    companies.id AS company_id,
    companies.name,
    companies.short_name,
    industries.name AS industry,
    securities.ticker,
    securities.exchange,
    EXISTS (
        SELECT 1
        FROM market_prices
        WHERE market_prices.security_id = securities.id
    ) AS has_market_prices,
    EXISTS (
        SELECT 1
        FROM financial_metrics
        WHERE financial_metrics.security_id = securities.id
    ) AS has_financial_metrics
FROM companies
JOIN securities ON securities.company_id = companies.id
LEFT JOIN industries ON industries.id = companies.industry_id
WHERE securities.is_active = TRUE
HAVING has_market_prices = TRUE OR has_financial_metrics = TRUE
ORDER BY securities.ticker;
"""

READ_COMPANY_MARKET_PRICES_SQL = """
SELECT
    market_prices.trade_date,
    market_prices.open_price,
    market_prices.high_price,
    market_prices.low_price,
    market_prices.close_price,
    market_prices.price_change,
    market_prices.volume,
    market_prices.trade_value,
    market_prices.transaction_count,
    market_prices.source,
    market_prices.fetched_at
FROM market_prices
JOIN securities ON securities.id = market_prices.security_id
WHERE securities.company_id = %s
ORDER BY market_prices.trade_date DESC
LIMIT %s;
"""

READ_COMPANY_FINANCIAL_METRICS_SQL = """
SELECT
    financial_metrics.report_date,
    financial_metrics.fiscal_year,
    financial_metrics.fiscal_quarter,
    financial_metrics.industry,
    financial_metrics.earnings_per_share,
    financial_metrics.face_value_text,
    financial_metrics.operating_revenue,
    financial_metrics.operating_income,
    financial_metrics.non_operating_income_expense,
    financial_metrics.net_income,
    financial_metrics.currency,
    financial_metrics.source,
    financial_metrics.fetched_at
FROM financial_metrics
JOIN securities ON securities.id = financial_metrics.security_id
WHERE securities.company_id = %s
ORDER BY
    financial_metrics.fiscal_year DESC,
    financial_metrics.fiscal_quarter DESC
LIMIT %s;
"""


def serialize_database_value(value):
    """將 MySQL 特殊型別轉成 Flask JSON 可安全輸出的值。"""
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")

    if isinstance(value, date):
        return value.isoformat()

    return value


def build_records(rows, column_names):
    """將 MySQL rows 轉成 JSON records。"""
    records = []

    for row in rows:
        record = {}

        for column_name, value in zip(column_names, row):
            record[column_name] = serialize_database_value(value)

        records.append(record)

    return records


def fetch_records(connection, query, parameters=()):
    """執行參數化查詢並建立 records。"""
    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return build_records(rows, column_names)


def fetch_market_companies(connection):
    """讀取至少已有一種市場資料的公司。"""
    records = fetch_records(connection, READ_MARKET_COMPANIES_SQL)

    for record in records:
        record["has_market_prices"] = bool(record["has_market_prices"])
        record["has_financial_metrics"] = bool(
            record["has_financial_metrics"]
        )

    return records


def validate_limit(limit):
    """限制單次 API 可讀取的歷史筆數。"""
    if not isinstance(limit, int) or limit < 1 or limit > 365:
        raise ValueError("limit 必須是 1 到 365 的整數。")


def fetch_company_market_prices(connection, company_id, limit=90):
    """讀取指定公司的最近每日價格。"""
    validate_limit(limit)
    return fetch_records(
        connection,
        READ_COMPANY_MARKET_PRICES_SQL,
        (company_id, limit),
    )


def fetch_company_financial_metrics(connection, company_id, limit=8):
    """讀取指定公司的最近季度財務摘要。"""
    validate_limit(limit)
    return fetch_records(
        connection,
        READ_COMPANY_FINANCIAL_METRICS_SQL,
        (company_id, limit),
    )


def load_company_market_data(loader, *arguments):
    """建立短連線執行一項公司市場資料查詢。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return loader(connection, *arguments)
    finally:
        connection.close()


def load_market_companies():
    """連接 MySQL 並讀取公司選單。"""
    return load_company_market_data(fetch_market_companies)


def load_company_market_prices(company_id, limit=90):
    """連接 MySQL 並讀取公司價格。"""
    return load_company_market_data(
        fetch_company_market_prices,
        company_id,
        limit,
    )


def load_company_financial_metrics(company_id, limit=8):
    """連接 MySQL 並讀取公司財務摘要。"""
    return load_company_market_data(
        fetch_company_financial_metrics,
        company_id,
        limit,
    )
