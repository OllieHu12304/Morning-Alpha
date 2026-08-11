"""定義 Morning Alpha 市場價格與財務資料的共同契約。"""


TWSE_PROVIDER = "臺灣證券交易所"
TWSE_EXCHANGE = "TWSE"
TWD_CURRENCY = "TWD"

MARKET_PRICE_SOURCE = {
    "name": "TWSE 上市個股日成交資訊",
    "provider": TWSE_PROVIDER,
    "url": (
        "https://openapi.twse.com.tw/v1/"
        "exchangeReport/STOCK_DAY_ALL"
    ),
    "update_frequency": "daily_after_market_close",
    "exchange": TWSE_EXCHANGE,
    "currency": TWD_CURRENCY,
    "license": "政府資料開放授權條款－第 1 版",
}

FINANCIAL_SOURCE = {
    "name": "TWSE 上市公司各產業 EPS 統計資訊",
    "provider": TWSE_PROVIDER,
    "url": (
        "https://openapi.twse.com.tw/v1/"
        "opendata/t187ap14_L"
    ),
    "update_frequency": "daily_poll_quarterly_content",
    "exchange": TWSE_EXCHANGE,
    "currency": TWD_CURRENCY,
    "license": "政府資料開放授權條款－第 1 版",
}

MARKET_PRICE_FIELD_MAP = {
    "Date": "trade_date",
    "Code": "ticker",
    "Name": "name",
    "TradeVolume": "volume",
    "TradeValue": "trade_value",
    "OpeningPrice": "open_price",
    "HighestPrice": "high_price",
    "LowestPrice": "low_price",
    "ClosingPrice": "close_price",
    "Change": "price_change",
    "Transaction": "transaction_count",
}

FINANCIAL_FIELD_MAP = {
    "出表日期": "report_date",
    "年度": "fiscal_year",
    "季別": "fiscal_quarter",
    "公司代號": "ticker",
    "公司名稱": "name",
    "產業別": "industry",
    "基本每股盈餘(元)": "earnings_per_share",
    "普通股每股面額": "face_value_text",
    "營業收入": "operating_revenue",
    "營業利益": "operating_income",
    "營業外收入及支出": "non_operating_income_expense",
    "稅後淨利": "net_income",
}

MARKET_PRICE_COMMON_FIELDS = [
    "ticker",
    "exchange",
    "trade_date",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "price_change",
    "volume",
    "trade_value",
    "transaction_count",
    "currency",
    "source",
    "fetched_at",
]

FINANCIAL_COMMON_FIELDS = [
    "ticker",
    "exchange",
    "report_date",
    "fiscal_year",
    "fiscal_quarter",
    "industry",
    "earnings_per_share",
    "face_value_text",
    "operating_revenue",
    "operating_income",
    "non_operating_income_expense",
    "net_income",
    "currency",
    "source",
    "fetched_at",
]


def find_missing_fields(record, required_fields):
    """列出來源紀錄中缺少或空白的必要欄位。"""
    if not isinstance(record, dict):
        raise ValueError("來源紀錄必須是 object。")

    return [
        field
        for field in required_fields
        if field not in record or str(record[field]).strip() == ""
    ]


def validate_source_contract(source_contract):
    """確認資料來源契約包含實作前需要的基本資訊。"""
    required_fields = [
        "name",
        "provider",
        "url",
        "update_frequency",
        "exchange",
        "currency",
        "license",
    ]
    missing_fields = find_missing_fields(source_contract, required_fields)

    if missing_fields:
        raise ValueError(
            "資料來源契約缺少欄位：" + ", ".join(missing_fields)
        )

    if not source_contract["url"].startswith(
        "https://openapi.twse.com.tw/v1/"
    ):
        raise ValueError("目前只接受 TWSE 官方 HTTPS OpenAPI。")

    return True
