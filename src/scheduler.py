"""定期執行 Morning Alpha Pipeline。"""

import os
from pathlib import Path
import subprocess
import sys
import time


DEFAULT_INTERVAL_HOURS = 24
PIPELINE_PATH = Path(__file__).resolve().parent / "run_pipeline.py"


def get_interval_seconds():
    """讀取正整數小時間隔，並轉成秒數。"""
    interval_text = os.getenv(
        "PIPELINE_INTERVAL_HOURS",
        str(DEFAULT_INTERVAL_HOURS),
    )

    try:
        interval_hours = int(interval_text)
    except ValueError as error:
        raise ValueError(
            "PIPELINE_INTERVAL_HOURS 必須是正整數。"
        ) from error

    if interval_hours < 1:
        raise ValueError("PIPELINE_INTERVAL_HOURS 必須是正整數。")

    return interval_hours * 60 * 60


def execute_pipeline():
    """使用目前 Python interpreter 執行一次 Pipeline。"""
    completed_process = subprocess.run(
        [sys.executable, str(PIPELINE_PATH)],
        check=False,
    )
    return completed_process.returncode


def run_scheduler(max_runs=None):
    """立即執行 Pipeline，之後依設定間隔重複執行。"""
    interval_seconds = get_interval_seconds()
    run_count = 0

    while max_runs is None or run_count < max_runs:
        print("Scheduler 開始執行 Pipeline。", flush=True)
        return_code = execute_pipeline()
        run_count += 1

        if return_code == 0:
            print("Scheduler：Pipeline 執行成功。", flush=True)
        else:
            print(
                f"Scheduler：Pipeline 執行失敗，exit code {return_code}。",
                flush=True,
            )

        if max_runs is not None and run_count >= max_runs:
            break

        print(
            f"Scheduler 將在 {interval_seconds // 3600} 小時後再次執行。",
            flush=True,
        )
        time.sleep(interval_seconds)


def main():
    """驗證設定並啟動長駐 scheduler。"""
    try:
        run_scheduler()
        return 0
    except ValueError as error:
        print(f"Scheduler 設定錯誤：{error}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
