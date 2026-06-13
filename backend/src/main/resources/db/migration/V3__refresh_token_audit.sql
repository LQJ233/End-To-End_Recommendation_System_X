-- V3: refresh_token 审计表 (可选, 仅记录签发与撤销事件, 真正的 token 状态走 Redis).

CREATE TABLE IF NOT EXISTS biz_refresh_token_audit (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     VARCHAR(64)  NOT NULL,
    token_id    VARCHAR(64)  NOT NULL,
    event       VARCHAR(32)  NOT NULL,        -- issue / rotate / revoke / expired
    client_ip   VARCHAR(64)  NULL,
    user_agent  VARCHAR(512) NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_refresh_user_time (user_id, created_at),
    KEY idx_refresh_token (token_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
