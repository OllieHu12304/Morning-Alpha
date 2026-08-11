-- 保存每日結構化晨報；同一 brief_date 只保留最新一次結果。
CREATE TABLE IF NOT EXISTS daily_briefs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brief_date DATE NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    article_count INT UNSIGNED NOT NULL,
    brief_payload JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_daily_brief_date (brief_date),
    INDEX index_daily_brief_updated_at (updated_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
