-- 第一步：先新增 nullable hash，讓 Python 可以安全稽核及回填。
-- 只執行一次；此步驟尚未建立 UNIQUE constraint。

ALTER TABLE news_records
    ADD COLUMN canonical_url_hash CHAR(64)
    CHARACTER SET ascii
    COLLATE ascii_bin
    NULL
    AFTER canonical_url;

SHOW COLUMNS FROM news_records;
