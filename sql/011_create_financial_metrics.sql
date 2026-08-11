-- 保存 TWSE 上市公司每季 EPS 與財務摘要。
CREATE TABLE IF NOT EXISTS financial_metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    security_id BIGINT UNSIGNED NOT NULL,
    report_date DATE NOT NULL,
    fiscal_year SMALLINT UNSIGNED NOT NULL,
    fiscal_quarter TINYINT UNSIGNED NOT NULL,
    industry VARCHAR(100) NULL,
    earnings_per_share DECIMAL(20, 4) NULL,
    face_value_text VARCHAR(100) NULL,
    operating_revenue DECIMAL(30, 2) NULL,
    operating_income DECIMAL(30, 2) NULL,
    non_operating_income_expense DECIMAL(30, 2) NULL,
    net_income DECIMAL(30, 2) NULL,
    currency CHAR(3) NOT NULL DEFAULT 'TWD',
    source VARCHAR(100) NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_security_fiscal_period (
        security_id,
        fiscal_year,
        fiscal_quarter
    ),
    INDEX index_financial_report_date (report_date),
    CONSTRAINT foreign_financial_metric_security
        FOREIGN KEY (security_id) REFERENCES securities (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
