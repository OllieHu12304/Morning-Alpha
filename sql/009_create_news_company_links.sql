-- 保存新聞與公司之間可解釋的多對多關聯。
CREATE TABLE IF NOT EXISTS news_company_links (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    news_id BIGINT UNSIGNED NOT NULL,
    company_id BIGINT UNSIGNED NOT NULL,
    matched_text VARCHAR(200) NOT NULL,
    match_method VARCHAR(30) NOT NULL,
    confidence DECIMAL(4, 3) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_news_company (news_id, company_id),
    INDEX index_news_company_company (company_id),
    CONSTRAINT foreign_news_company_news
        FOREIGN KEY (news_id) REFERENCES news_records (id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT foreign_news_company_company
        FOREIGN KEY (company_id) REFERENCES companies (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
