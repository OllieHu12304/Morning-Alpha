"""定義 Morning Alpha 每日晨報的固定時間範圍。"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


BRIEF_TIMEZONE = ZoneInfo("Asia/Taipei")
BRIEF_HOUR = 7


def get_latest_brief_date(current_time=None):
    """依台北時間取得最近一個已完成晨報的日期。"""
    if current_time is None:
        current_time = datetime.now(BRIEF_TIMEZONE)

    if current_time.tzinfo is None:
        raise ValueError("current_time 必須包含 timezone。")

    taipei_time = current_time.astimezone(BRIEF_TIMEZONE)
    brief_date = taipei_time.date()

    if taipei_time.hour < BRIEF_HOUR:
        brief_date -= timedelta(days=1)

    return brief_date


def get_brief_window(brief_date):
    """取得指定晨報日期前 24 小時的台北時間範圍。"""
    if not isinstance(brief_date, date) or isinstance(brief_date, datetime):
        raise ValueError("brief_date 必須是 date。")

    end_time = datetime.combine(
        brief_date,
        time(hour=BRIEF_HOUR),
        tzinfo=BRIEF_TIMEZONE,
    )
    start_time = end_time - timedelta(days=1)
    return start_time, end_time


def to_database_datetime(value):
    """將 timezone-aware datetime 轉成 MySQL 使用的台北 naive datetime。"""
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("value 必須是包含 timezone 的 datetime。")

    taipei_time = value.astimezone(BRIEF_TIMEZONE)
    return taipei_time.replace(tzinfo=None)
