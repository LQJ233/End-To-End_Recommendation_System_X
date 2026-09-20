CREATE TABLE IF NOT EXISTS model_registry (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    model_name VARCHAR(64) NOT NULL,
    version VARCHAR(64) NOT NULL,
    artifact_path VARCHAR(500) NOT NULL,
    metrics_json TEXT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_model_version (model_name, version)
);
