-- 保存每次完整 Pipeline 的執行結果與各步驟摘要。

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    started_at DATETIME(6) NOT NULL,
    finished_at DATETIME(6) NOT NULL,
    duration_ms BIGINT UNSIGNED NOT NULL,
    failed_step VARCHAR(100) NULL,
    step_results JSON NOT NULL,
    error_message VARCHAR(500) NULL,
    INDEX index_pipeline_started_at (started_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
