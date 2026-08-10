"""設定 Morning Alpha 終端與檔案 logging。"""

import logging
from pathlib import Path


LOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "morning_alpha.log"
)


def configure_logging(log_path=LOG_PATH):
    """建立一致的 console 與 UTF-8 log file 設定。"""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )
