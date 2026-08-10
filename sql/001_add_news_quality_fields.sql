-- Morning Alpha news_records 資料品質欄位 migration。
-- 只適用於尚未包含這四個欄位的既有 database，且只執行一次。

ALTER TABLE news_records
    ADD COLUMN source VARCHAR(100) NULL AFTER id,
    ADD COLUMN source_category VARCHAR(100) NULL AFTER source,
    ADD COLUMN analysis_category VARCHAR(100) NULL AFTER source_category,
    ADD COLUMN canonical_url VARCHAR(1000) NULL AFTER url;

-- 現有 Morning Alpha v0.1 資料全部來自 TechNews。
UPDATE news_records
SET source = 'technews'
WHERE source IS NULL;

-- URL normalization 會由後續 feature 完成；目前先保留原始 URL。
UPDATE news_records
SET canonical_url = url
WHERE canonical_url IS NULL;

ALTER TABLE news_records
    MODIFY COLUMN source VARCHAR(100) NOT NULL,
    MODIFY COLUMN canonical_url VARCHAR(1000) NOT NULL;

-- 執行後的人工驗證結果應為 0。
SELECT COUNT(*) AS rows_missing_quality_fields
FROM news_records
WHERE source IS NULL OR canonical_url IS NULL;

SHOW COLUMNS FROM news_records;
