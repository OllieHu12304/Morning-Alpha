-- 第三步：只在 002 migration 與 Python backfill 成功後執行一次。
-- 下列查詢應分別回傳 0 筆及空結果，才能繼續 ALTER TABLE。

SELECT COUNT(*) AS rows_missing_canonical_hash
FROM news_records
WHERE canonical_url_hash IS NULL;

SELECT canonical_url_hash, COUNT(*) AS duplicate_count
FROM news_records
GROUP BY canonical_url_hash
HAVING COUNT(*) > 1;

ALTER TABLE news_records
    MODIFY COLUMN canonical_url_hash CHAR(64)
    CHARACTER SET ascii
    COLLATE ascii_bin
    NOT NULL,
    ADD UNIQUE KEY unique_canonical_url_hash (canonical_url_hash);

SHOW INDEX FROM news_records;
