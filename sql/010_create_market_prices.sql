-- 保存 TWSE 上市公司每日盤後價格與成交資訊。
CREATE TABLE IF NOT EXISTS market_prices (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    security_id BIGINT UNSIGNED NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(18, 4) NULL,
    high_price DECIMAL(18, 4) NULL,
    low_price DECIMAL(18, 4) NULL,
    close_price DECIMAL(18, 4) NULL,
    price_change DECIMAL(18, 4) NULL,
    volume BIGINT UNSIGNED NULL,
    trade_value DECIMAL(24, 2) NULL,
    transaction_count BIGINT UNSIGNED NULL,
    source VARCHAR(100) NOT NULL,
    fetched_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_security_trade_date (security_id, trade_date),
    INDEX index_market_price_trade_date (trade_date),
    CONSTRAINT foreign_market_price_security
        FOREIGN KEY (security_id) REFERENCES securities (id)
        ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
