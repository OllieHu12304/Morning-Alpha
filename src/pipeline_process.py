"""從 Dashboard 安全地啟動並追蹤單一 Pipeline subprocess。"""

import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = PROJECT_DIRECTORY / "src" / "run_pipeline.py"

_pipeline_lock = threading.Lock()
_pipeline_process = None
_pipeline_started_at = None
_pipeline_finished_at = None


def utc_now_iso():
    """回傳可直接放入 JSON 的 UTC 時間。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_pipeline_status():
    """依目前 subprocess 狀態建立 API response。"""
    global _pipeline_finished_at

    if _pipeline_process is None:
        return {
            "status": "idle",
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
        }

    exit_code = _pipeline_process.poll()

    if exit_code is None:
        status = "running"
    else:
        status = "success" if exit_code == 0 else "failure"

        if _pipeline_finished_at is None:
            _pipeline_finished_at = utc_now_iso()

    return {
        "status": status,
        "started_at": _pipeline_started_at,
        "finished_at": _pipeline_finished_at,
        "exit_code": exit_code,
    }


def get_pipeline_status():
    """以 lock 保護並回傳目前 Pipeline 狀態。"""
    with _pipeline_lock:
        return build_pipeline_status()


def start_pipeline():
    """使用目前 Python 環境啟動 Pipeline；執行中時拒絕重複啟動。"""
    global _pipeline_process
    global _pipeline_started_at
    global _pipeline_finished_at

    with _pipeline_lock:
        current_status = build_pipeline_status()

        if current_status["status"] == "running":
            return False, current_status

        if not PIPELINE_SCRIPT.is_file():
            raise OSError("找不到 Pipeline script。")

        _pipeline_process = subprocess.Popen(
            [sys.executable, str(PIPELINE_SCRIPT)],
            cwd=PROJECT_DIRECTORY,
        )
        _pipeline_started_at = utc_now_iso()
        _pipeline_finished_at = None

        return True, build_pipeline_status()
