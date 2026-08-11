"""保存並讀取完整 Pipeline 的執行歷史。"""

import json
from datetime import datetime, timezone

import pymysql

from store_news import connect_to_database, get_database_config


MAX_ERROR_LENGTH = 500
VALID_RUN_STATUSES = {"success", "failure"}
VALID_STEP_STATUSES = {"pending", "success", "failure"}
LEGACY_PIPELINE_STEPS = [
    ("collect_news", "爬取、整理並儲存新聞"),
    ("export_news", "匯出 Dashboard 新聞資料"),
    ("chart_data", "產生 Dashboard 圖表資料"),
    ("keywords", "產生 Top 20 關鍵字資料"),
]
PIPELINE_STEPS = [
    ("collect_news", "爬取、整理並儲存新聞"),
    ("sync_companies", "同步 TWSE 公司資料"),
    ("link_news_companies", "建立新聞公司關聯"),
    ("sync_market_prices", "同步 TWSE 每日價格"),
    ("sync_financial_metrics", "同步 TWSE 財務摘要"),
    ("daily_brief", "產生並保存每日晨報"),
    ("export_news", "匯出 Dashboard 新聞資料"),
    ("chart_data", "產生 Dashboard 圖表資料"),
    ("keywords", "產生 Top 20 關鍵字資料"),
]

CREATE_PIPELINE_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    started_at DATETIME(6) NOT NULL,
    finished_at DATETIME(6) NOT NULL,
    duration_ms BIGINT UNSIGNED NOT NULL,
    failed_step VARCHAR(100) NULL,
    step_results JSON NOT NULL,
    error_message VARCHAR(500) NULL,
    INDEX index_pipeline_started_at (started_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

INSERT_PIPELINE_RUN_SQL = """
INSERT INTO pipeline_runs (
    status,
    started_at,
    finished_at,
    duration_ms,
    failed_step,
    step_results,
    error_message
)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

READ_PIPELINE_RUNS_SQL = """
SELECT
    id,
    status,
    started_at,
    finished_at,
    duration_ms,
    failed_step,
    step_results,
    error_message
FROM pipeline_runs
ORDER BY started_at DESC, id DESC
LIMIT %s;
"""


def create_pending_step_results():
    """建立目前九個尚未執行的固定 Pipeline steps。"""
    results = []

    for step, label in PIPELINE_STEPS:
        results.append({
            "step": step,
            "label": label,
            "status": "pending",
            "duration_ms": None,
            "summary": None,
        })

    return results


def utc_now():
    """取得適合寫入 MySQL DATETIME 的 UTC naive datetime。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def update_step_result(
    step_results,
    step,
    status,
    duration_ms,
    summary=None,
):
    """更新指定步驟；找不到步驟時拒絕靜默新增。"""
    if status not in {"success", "failure"}:
        raise ValueError("Pipeline step status 必須是 success 或 failure。")

    if not isinstance(duration_ms, int) or duration_ms < 0:
        raise ValueError("Pipeline step duration_ms 必須是非負整數。")

    for result in step_results:
        if result["step"] == step:
            result["status"] = status
            result["duration_ms"] = duration_ms
            result["summary"] = summary
            return

    raise ValueError(f"找不到 Pipeline step：{step}")


def clean_error_message(error_message):
    """清除換行並限制 Dashboard 可見的錯誤長度。"""
    if not error_message:
        return "未知 Pipeline 錯誤"

    cleaned_message = " ".join(str(error_message).split())
    return cleaned_message[:MAX_ERROR_LENGTH]


def validate_step_results(step_results):
    """確認目前九步驟或舊版四步驟歷史可安全讀取。"""
    if not isinstance(step_results, list):
        raise ValueError("Pipeline step_results 必須是 list。")

    actual_definitions = []

    for result in step_results:
        if not isinstance(result, dict):
            raise ValueError("Pipeline step_result 必須是 object。")

        step = result.get("step")
        status = result.get("status")
        duration_ms = result.get("duration_ms")
        label = result.get("label")
        actual_definitions.append((step, label))

        if status not in VALID_STEP_STATUSES:
            raise ValueError("Pipeline step_result status 無效。")

        if status == "pending" and duration_ms is not None:
            raise ValueError("尚未執行的 Pipeline step 不可有 duration_ms。")

        if status != "pending" and (
            not isinstance(duration_ms, int) or duration_ms < 0
        ):
            raise ValueError("Pipeline step_result duration_ms 無效。")

    known_definitions = [PIPELINE_STEPS, LEGACY_PIPELINE_STEPS]

    if actual_definitions not in known_definitions:
        raise ValueError("Pipeline step_results 順序或名稱不正確。")

    return actual_definitions


def prepare_pipeline_run_record(run_result):
    """驗證執行結果並轉成 PyMySQL parameter tuple。"""
    status = run_result.get("status")
    started_at = run_result.get("started_at")
    finished_at = run_result.get("finished_at")
    duration_ms = run_result.get("duration_ms")
    failed_step = run_result.get("failed_step")
    step_results = run_result.get("step_results")
    error_message = run_result.get("error_message")

    if status not in VALID_RUN_STATUSES:
        raise ValueError("Pipeline run status 必須是 success 或 failure。")

    if not isinstance(started_at, datetime) or not isinstance(finished_at, datetime):
        raise ValueError("Pipeline run 時間必須是 datetime。")

    if finished_at < started_at:
        raise ValueError("Pipeline finished_at 不可早於 started_at。")

    if not isinstance(duration_ms, int) or duration_ms < 0:
        raise ValueError("Pipeline duration_ms 必須是非負整數。")

    step_definitions = validate_step_results(step_results)
    step_statuses = {
        result["step"]: result["status"]
        for result in step_results
    }

    if status == "success":
        if any(step_status != "success" for step_status in step_statuses.values()):
            raise ValueError("成功的 Pipeline run 不可包含未完成步驟。")

        failed_step = None
        error_message = None
    else:
        if failed_step not in step_statuses:
            raise ValueError("失敗的 Pipeline run 必須提供 failed_step。")

        if step_statuses[failed_step] != "failure":
            raise ValueError("failed_step 必須對應 failure 步驟。")

        step_names = [step for step, _ in step_definitions]
        failed_index = step_names.index(failed_step)
        expected_statuses = (
            ["success"] * failed_index
            + ["failure"]
            + ["pending"] * (len(step_definitions) - failed_index - 1)
        )

        if list(step_statuses.values()) != expected_statuses:
            raise ValueError("失敗的 Pipeline step 狀態順序不正確。")

        error_message = clean_error_message(error_message)

    step_results_json = json.dumps(step_results, ensure_ascii=False)

    return (
        status,
        started_at,
        finished_at,
        duration_ms,
        failed_step,
        step_results_json,
        error_message,
    )


def create_pipeline_runs_table(connection):
    """建立 Pipeline history table。"""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_PIPELINE_RUNS_TABLE_SQL)


def insert_pipeline_run(connection, run_result):
    """新增一筆已完成的 Pipeline run。"""
    record = prepare_pipeline_run_record(run_result)

    with connection.cursor() as cursor:
        cursor.execute(INSERT_PIPELINE_RUN_SQL, record)
        return cursor.lastrowid


def save_pipeline_run(run_result):
    """用獨立 transaction 保存一筆 Pipeline run。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        create_pipeline_runs_table(connection)
        run_id = insert_pipeline_run(connection, run_result)
        connection.commit()
        return run_id
    except (pymysql.MySQLError, TypeError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_pipeline_runs(connection, limit=10):
    """依最新到最舊讀取指定數量的 Pipeline runs。"""
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValueError("Pipeline history limit 必須介於 1 到 100。")

    with connection.cursor() as cursor:
        cursor.execute(READ_PIPELINE_RUNS_SQL, (limit,))
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return rows, column_names


def load_pipeline_runs(limit=10):
    """連接 MySQL 並讀取 Pipeline runs。"""
    config = get_database_config()
    connection = connect_to_database(config)

    try:
        return fetch_pipeline_runs(connection, limit=limit)
    finally:
        connection.close()


def format_datetime(value):
    """將 MySQL UTC datetime 轉成帶有 UTC offset 的 ISO 文字。"""
    if isinstance(value, datetime):
        utc_value = value.replace(tzinfo=timezone.utc)
        return utc_value.isoformat(timespec="seconds")

    return None


def build_pipeline_run_records(rows, column_names):
    """將 MySQL rows 轉成 API 可回傳的執行紀錄。"""
    records = []

    for row in rows:
        record = dict(zip(column_names, row))
        step_results = record["step_results"]

        if record["status"] not in VALID_RUN_STATUSES:
            raise ValueError("MySQL Pipeline run status 無效。")

        if not isinstance(record["duration_ms"], int) or record["duration_ms"] < 0:
            raise ValueError("MySQL Pipeline duration_ms 無效。")

        if isinstance(step_results, str):
            step_results = json.loads(step_results)

        validate_step_results(step_results)
        records.append({
            "id": record["id"],
            "status": record["status"],
            "started_at": format_datetime(record["started_at"]),
            "finished_at": format_datetime(record["finished_at"]),
            "duration_ms": record["duration_ms"],
            "failed_step": record["failed_step"],
            "step_results": step_results,
            "error_message": record["error_message"],
        })

    return records
