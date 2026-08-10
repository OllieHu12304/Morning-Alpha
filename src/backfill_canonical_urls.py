"""稽核並選擇性回填既有新聞的 canonical URL 與 hash。"""

import json
import sys
from pathlib import Path

import pymysql

from canonical_url_hash import create_canonical_url_hash
from store_news import connect_to_database, get_database_config
from url_normalizer import normalize_url


REPORT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "canonical_url_audit.json"
)

READ_NEWS_SQL = """
SELECT id, title, url, canonical_url
FROM news_records
ORDER BY id;
"""

UPDATE_CANONICAL_URL_SQL = """
UPDATE news_records
SET canonical_url = %s,
    canonical_url_hash = %s
WHERE id = %s;
"""


def fetch_news_records(connection):
    """讀取 backfill 需要的新聞欄位。"""
    with connection.cursor() as cursor:
        cursor.execute(READ_NEWS_SQL)
        rows = cursor.fetchall()

    records = []

    for row in rows:
        records.append({
            "id": row[0],
            "title": row[1],
            "url": row[2],
            "canonical_url": row[3],
        })

    return records


def build_backfill_plan(records):
    """建立更新內容及不會修改 database 的稽核報告。"""
    updates = []
    invalid_records = []
    canonical_groups = {}
    changed_urls = 0

    for record in records:
        try:
            normalized_url = normalize_url(record["url"])
            url_hash = create_canonical_url_hash(normalized_url)
        except ValueError as error:
            invalid_records.append({
                "id": record["id"],
                "title": record["title"],
                "url": record["url"],
                "error": str(error),
            })
            continue

        if normalized_url != record["canonical_url"]:
            changed_urls += 1

        update = {
            "id": record["id"],
            "canonical_url": normalized_url,
            "canonical_url_hash": url_hash,
        }
        updates.append(update)

        group_record = {
            "id": record["id"],
            "title": record["title"],
            "url": record["url"],
        }
        canonical_groups.setdefault(normalized_url, []).append(group_record)

    conflict_groups = []

    for canonical_url in sorted(canonical_groups):
        group_records = canonical_groups[canonical_url]

        if len(group_records) > 1:
            conflict_groups.append({
                "canonical_url": canonical_url,
                "records": group_records,
            })

    report = {
        "total_records": len(records),
        "valid_records": len(updates),
        "changed_urls": changed_urls,
        "invalid_records": invalid_records,
        "conflict_groups": conflict_groups,
    }

    return report, updates


def export_audit_report(report, output_path=REPORT_PATH):
    """將稽核結果輸出成 UTF-8 JSON。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(report, json_file, ensure_ascii=False, indent=2)


def apply_backfill(connection, updates):
    """使用 parameterized UPDATE 寫入已確認無衝突的結果。"""
    parameters = []

    for update in updates:
        parameters.append((
            update["canonical_url"],
            update["canonical_url_hash"],
            update["id"],
        ))

    if not parameters:
        return 0

    with connection.cursor() as cursor:
        return cursor.executemany(UPDATE_CANONICAL_URL_SQL, parameters)


def run_backfill(apply_changes=False):
    """預設只稽核；apply_changes=True 時才更新 MySQL。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        records = fetch_news_records(connection)
        report, updates = build_backfill_plan(records)
        export_audit_report(report)

        if not apply_changes:
            return report, 0

        if report["invalid_records"]:
            raise ValueError("存在無效 URL，已停止 backfill。")

        if report["conflict_groups"]:
            raise ValueError("存在 canonical URL 衝突，已停止 backfill。")

        updated_count = apply_backfill(connection, updates)
        connection.commit()
        return report, updated_count
    except (pymysql.MySQLError, OSError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def print_report_summary(report, updated_count):
    """顯示稽核或 backfill 結果。"""
    print(f"新聞總數：{report['total_records']} 筆")
    print(f"有效 URL：{report['valid_records']} 筆")
    print(f"需要正規化：{report['changed_urls']} 筆")
    print(f"無效 URL：{len(report['invalid_records'])} 筆")
    print(f"Canonical URL 衝突：{len(report['conflict_groups'])} 組")
    print(f"已更新 MySQL：{updated_count} 筆")
    print(f"稽核報告：{REPORT_PATH}")


def main(arguments=None):
    """解析 --apply，預設執行安全的唯讀稽核。"""
    if arguments is None:
        arguments = sys.argv[1:]

    if arguments == []:
        apply_changes = False
    elif arguments == ["--apply"]:
        apply_changes = True
    else:
        print("用法：python3 src/backfill_canonical_urls.py [--apply]")
        return 2

    try:
        report, updated_count = run_backfill(apply_changes)
        print_report_summary(report, updated_count)
        return 0
    except pymysql.MySQLError as error:
        print(f"Canonical URL backfill 失敗：MySQL 錯誤：{error}")
    except ValueError as error:
        print(f"Canonical URL backfill 失敗：{error}")
    except OSError as error:
        print(f"Canonical URL backfill 失敗：檔案錯誤：{error}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
