"""以一個初學者友善指令啟動 Morning Alpha Dashboard。"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent
API_SCRIPT = PROJECT_DIRECTORY / "src" / "api.py"
DASHBOARD_URL = "http://127.0.0.1:5050"
HEALTH_URL = f"{DASHBOARD_URL}/api/health"
API_HOST = "127.0.0.1"
API_PORT = 5050
STARTUP_TIMEOUT_SECONDS = 15
HEALTH_CHECK_INTERVAL_SECONDS = 0.2


def find_venv_python(project_directory):
    """尋找 macOS/Linux 或 Windows 的 project virtual environment。"""
    candidates = [
        project_directory / ".venv" / "bin" / "python",
        project_directory / ".venv" / "Scripts" / "python.exe",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return None


def has_database_config(project_directory):
    """確認使用者已建立 .env，或已在 shell 設定 MySQL 帳密。"""
    env_file = project_directory / ".env"

    if env_file.is_file():
        return True

    return bool(os.getenv("MYSQL_USER") and os.getenv("MYSQL_PASSWORD"))


def is_morning_alpha_running():
    """確認 5050 是否已由 Morning Alpha API 提供服務。"""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=0.5) as response:
            payload = json.load(response)
    except (
        json.JSONDecodeError,
        OSError,
        TimeoutError,
        urllib.error.URLError,
        ValueError,
    ):
        return False

    return payload == {"status": "ok"}


def is_api_port_in_use():
    """檢查 5050 是否已被其他程式占用。"""
    try:
        with socket.create_connection((API_HOST, API_PORT), timeout=0.5):
            return True
    except OSError:
        return False


def wait_for_api(process):
    """等待 Flask API 就緒，或偵測啟動程序提前結束。"""
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False

        if is_morning_alpha_running():
            return True

        time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    return False


def stop_api_process(process):
    """先溫和停止 API，逾時時再強制結束。"""
    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def open_dashboard():
    """開啟預設瀏覽器；失敗時保留可手動開啟的網址。"""
    opened = webbrowser.open(DASHBOARD_URL)

    if opened:
        print(f"Dashboard 已開啟：{DASHBOARD_URL}")
    else:
        print(f"請在瀏覽器開啟：{DASHBOARD_URL}")


def run():
    """檢查環境、啟動 API 並保持執行直到使用者停止。"""
    if is_morning_alpha_running():
        print("Morning Alpha 已在 5050 執行，不會重複啟動。")
        open_dashboard()
        return 0

    if is_api_port_in_use():
        print("無法啟動：5050 port 已被其他程式占用。")
        print("請先停止該程式，再重新執行 python3 start.py。")
        return 1

    venv_python = find_venv_python(PROJECT_DIRECTORY)

    if venv_python is None:
        print("找不到 .venv Python。請先完成虛擬環境安裝：")
        print("python3 -m venv .venv")
        print("./.venv/bin/python -m pip install -r requirements.txt")
        return 1

    if not has_database_config(PROJECT_DIRECTORY):
        print("找不到 MySQL 設定。請先建立 .env：")
        print("cp .env.example .env")
        print("再將 Morning Alpha MySQL app user 的密碼填入 .env。")
        return 1

    print("正在啟動 Morning Alpha API…")
    try:
        process = subprocess.Popen(
            [str(venv_python), str(API_SCRIPT)],
            cwd=PROJECT_DIRECTORY,
        )
    except OSError as error:
        print(f"無法啟動 API：{error}")
        return 1

    try:
        if not wait_for_api(process):
            print("API 未能在 15 秒內啟動，請查看上方錯誤訊息。")
            stop_api_process(process)
            return 1

        open_dashboard()
        print("Morning Alpha 執行中；按 Control + C 即可停止。")
        return process.wait()
    except KeyboardInterrupt:
        print("\n正在停止 Morning Alpha…")
        stop_api_process(process)
        print("Morning Alpha 已停止。")
        return 0


def main():
    """提供可由 terminal 執行的 exit code。"""
    return run()


if __name__ == "__main__":
    sys.exit(main())
