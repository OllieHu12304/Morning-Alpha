-- 區分資料取得管道與原始發布媒體，並保存來源文章識別碼。
ALTER TABLE news_records
    ADD COLUMN publisher VARCHAR(100) NULL AFTER source,
    ADD COLUMN source_article_id VARCHAR(255) NULL AFTER publisher;

-- 既有來源都是直接來源，因此可安全以 source 回填 publisher。
UPDATE news_records
SET publisher = source
WHERE publisher IS NULL;

ALTER TABLE news_records
    MODIFY COLUMN publisher VARCHAR(100) NOT NULL,
    ADD UNIQUE KEY unique_source_article (
        source,
        source_article_id
    ),
    ADD INDEX index_news_publisher (publisher);
