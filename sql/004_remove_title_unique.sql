-- Canonical URL 已成為新聞文章的唯一識別依據後，移除舊的標題 UNIQUE。
-- 執行前應先完成 002、Python backfill 與 003 migration。

-- 執行前確認兩個 index 都存在。
SHOW INDEX FROM news_records
WHERE Key_name IN ('unique_news_title', 'unique_canonical_url_hash');

ALTER TABLE news_records
    DROP INDEX unique_news_title;

-- 執行後應只查到 unique_canonical_url_hash。
SHOW INDEX FROM news_records
WHERE Key_name IN ('unique_news_title', 'unique_canonical_url_hash');
