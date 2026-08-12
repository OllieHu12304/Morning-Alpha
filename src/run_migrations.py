"""檢查並選擇性套用 Morning Alpha MySQL migrations。"""

import sys
from pathlib import Path

import pymysql

from backfill_canonical_urls import run_backfill
from store_news import connect_to_database, get_database_config


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
MIGRATION_DIRECTORY = PROJECT_DIRECTORY / "sql"
MIGRATION_PATHS = {
    "001": MIGRATION_DIRECTORY / "001_add_news_quality_fields.sql",
    "002": MIGRATION_DIRECTORY / "002_add_canonical_url_hash.sql",
    "003": MIGRATION_DIRECTORY / "003_enforce_canonical_url_uniqueness.sql",
    "004": MIGRATION_DIRECTORY / "004_remove_title_unique.sql",
    "005": MIGRATION_DIRECTORY / "005_create_source_health_events.sql",
    "006": MIGRATION_DIRECTORY / "006_create_pipeline_runs.sql",
    "007": MIGRATION_DIRECTORY / "007_create_daily_briefs.sql",
    "008": MIGRATION_DIRECTORY / "008_create_company_directory.sql",
    "009": MIGRATION_DIRECTORY / "009_create_news_company_links.sql",
    "010": MIGRATION_DIRECTORY / "010_create_market_prices.sql",
    "011": MIGRATION_DIRECTORY / "011_create_financial_metrics.sql",
    "012": MIGRATION_DIRECTORY / "012_create_watchlist_items.sql",
    "013": MIGRATION_DIRECTORY / "013_add_article_identity.sql",
}
INDEPENDENT_MIGRATIONS = {"005", "006", "007", "008"}


def fetch_schema_state(connection):
    """從 MySQL 欄位與 index 判斷 migration 實際狀態。"""
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE 'news_records';")
        table_exists = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'source_health_events';")
        source_health_exists = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'pipeline_runs';")
        pipeline_runs_exists = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'daily_briefs';")
        daily_briefs_exists = cursor.fetchone() is not None

        company_directory_exists = True

        for table_name in [
            "industries",
            "companies",
            "securities",
            "company_aliases",
        ]:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}';")

            if cursor.fetchone() is None:
                company_directory_exists = False

        cursor.execute("SHOW TABLES LIKE 'news_company_links';")
        news_company_links_exists = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'market_prices';")
        market_prices_exists = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'financial_metrics';")
        financial_metrics_exists = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'watchlist_items';")
        watchlist_items_exists = cursor.fetchone() is not None

        if not table_exists:
            return {
                "table_exists": False,
                "columns": set(),
                "indexes": set(),
                "source_health_exists": source_health_exists,
                "pipeline_runs_exists": pipeline_runs_exists,
                "daily_briefs_exists": daily_briefs_exists,
                "company_directory_exists": company_directory_exists,
                "news_company_links_exists": news_company_links_exists,
                "market_prices_exists": market_prices_exists,
                "financial_metrics_exists": financial_metrics_exists,
                "watchlist_items_exists": watchlist_items_exists,
            }

        cursor.execute("SHOW COLUMNS FROM news_records;")
        columns = {row[0] for row in cursor.fetchall()}

        cursor.execute("SHOW INDEX FROM news_records;")
        indexes = {row[2] for row in cursor.fetchall()}

    return {
        "table_exists": True,
        "columns": columns,
        "indexes": indexes,
        "source_health_exists": source_health_exists,
        "pipeline_runs_exists": pipeline_runs_exists,
        "daily_briefs_exists": daily_briefs_exists,
        "company_directory_exists": company_directory_exists,
        "news_company_links_exists": news_company_links_exists,
        "market_prices_exists": market_prices_exists,
        "financial_metrics_exists": financial_metrics_exists,
        "watchlist_items_exists": watchlist_items_exists,
    }


def get_migration_status(schema_state):
    """將目前 schema 轉成 001 到 013 的完成狀態。"""
    columns = schema_state["columns"]
    indexes = schema_state["indexes"]
    quality_columns = {
        "source",
        "source_category",
        "analysis_category",
        "canonical_url",
    }
    canonical_unique_exists = "unique_canonical_url_hash" in indexes

    return {
        "001": quality_columns.issubset(columns),
        "002": "canonical_url_hash" in columns,
        "003": canonical_unique_exists,
        "004": canonical_unique_exists and "unique_news_title" not in indexes,
        "005": schema_state.get("source_health_exists", False),
        "006": schema_state.get("pipeline_runs_exists", False),
        "007": schema_state.get("daily_briefs_exists", False),
        "008": schema_state.get("company_directory_exists", False),
        "009": schema_state.get("news_company_links_exists", False),
        "010": schema_state.get("market_prices_exists", False),
        "011": schema_state.get("financial_metrics_exists", False),
        "012": schema_state.get("watchlist_items_exists", False),
        "013": (
            {"publisher", "source_article_id"}.issubset(columns)
            and "unique_source_article" in indexes
            and "index_news_publisher" in indexes
        ),
    }


def validate_schema_state(schema_state):
    """拒絕自動處理只完成一部分的 001 schema。"""
    quality_columns = {
        "source",
        "source_category",
        "analysis_category",
        "canonical_url",
    }
    existing_quality_columns = quality_columns & schema_state["columns"]

    if existing_quality_columns and existing_quality_columns != quality_columns:
        raise ValueError(
            "偵測到部分 news quality 欄位，請先人工檢查 schema。"
        )

    identity_columns = {"publisher", "source_article_id"}
    existing_identity_columns = identity_columns & schema_state["columns"]
    identity_indexes = {
        "unique_source_article",
        "index_news_publisher",
    }
    existing_identity_indexes = identity_indexes & schema_state["indexes"]

    if (
        existing_identity_columns
        and existing_identity_columns != identity_columns
    ):
        raise ValueError(
            "偵測到部分 article identity 欄位，請先人工檢查 schema。"
        )

    if (
        existing_identity_columns == identity_columns
        and existing_identity_indexes != identity_indexes
    ):
        raise ValueError(
            "偵測到部分 article identity indexes，請先人工檢查 schema。"
        )


def split_sql_statements(sql_text):
    """移除整行註解並將簡單 migration SQL 按分號切開。"""
    sql_lines = []

    for line in sql_text.splitlines():
        if line.strip().startswith("--"):
            continue

        sql_lines.append(line)

    statements = []

    for statement in "\n".join(sql_lines).split(";"):
        statement = statement.strip()

        if statement:
            statements.append(statement)

    return statements


def execute_migration(connection, migration_path):
    """逐一執行 migration 檔案內的 SQL statements。"""
    sql_text = migration_path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_text)

    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)

    connection.commit()


def print_status(schema_state):
    """以初學者容易閱讀的方式顯示 migration 狀態。"""
    if not schema_state["table_exists"]:
        print("news_records 尚未建立；第一次執行 Pipeline 會建立最新 schema。")

    migration_status = get_migration_status(schema_state)

    for migration_number in MIGRATION_PATHS:
        if (
            not schema_state["table_exists"]
            and migration_number not in INDEPENDENT_MIGRATIONS
        ):
            continue

        status_label = "完成" if migration_status[migration_number] else "待執行"
        print(f"Migration {migration_number}：{status_label}")


def apply_pending_migrations(connection):
    """依安全順序套用目前尚未完成的 migrations。"""
    schema_state = fetch_schema_state(connection)

    if schema_state["table_exists"]:
        validate_schema_state(schema_state)

    migration_status = get_migration_status(schema_state)

    for migration_number in MIGRATION_PATHS:
        if (
            not schema_state["table_exists"]
            and migration_number not in INDEPENDENT_MIGRATIONS
        ):
            continue

        if migration_status[migration_number]:
            print(f"Migration {migration_number} 已完成，跳過。")
            continue

        if migration_number == "003":
            print("執行 Canonical URL 稽核與 backfill…")
            report, updated_count = run_backfill(apply_changes=True)
            print(f"Canonical URL backfill 更新：{updated_count} 筆")

            if report["invalid_records"] or report["conflict_groups"]:
                raise ValueError("Canonical URL 稽核未通過，停止 migration。")

        migration_path = MIGRATION_PATHS[migration_number]
        print(f"套用 Migration {migration_number}：{migration_path.name}")
        execute_migration(connection, migration_path)
        migration_status[migration_number] = True


def run(apply_changes=False):
    """連接 MySQL；預設只查狀態，--apply 才修改 schema。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        if apply_changes:
            apply_pending_migrations(connection)

        schema_state = fetch_schema_state(connection)
        print_status(schema_state)
    except (pymysql.MySQLError, OSError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def main(arguments=None):
    """解析安全的唯讀模式或明確的 --apply。"""
    if arguments is None:
        arguments = sys.argv[1:]

    if arguments == []:
        apply_changes = False
    elif arguments == ["--apply"]:
        apply_changes = True
    else:
        print("用法：python3 src/run_migrations.py [--apply]")
        return 2

    try:
        run(apply_changes=apply_changes)
        return 0
    except pymysql.MySQLError as error:
        print(f"Migration 失敗：MySQL 錯誤：{error}")
    except ValueError as error:
        print(f"Migration 失敗：{error}")
    except OSError as error:
        print(f"Migration 失敗：檔案錯誤：{error}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
