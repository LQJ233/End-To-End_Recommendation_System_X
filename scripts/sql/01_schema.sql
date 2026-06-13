-- end_to_end_recommendation_system_x schema (MySQL 8.x)
CREATE DATABASE IF NOT EXISTS end_to_end_recommendation_system_x DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE end_to_end_recommendation_system_x;

-- =============== 鍘熷澶╂睜鏁版嵁琛?===============
CREATE TABLE IF NOT EXISTS tianchi_mobile_recommend_train_user (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    user_id       VARCHAR(64)  NOT NULL,
    item_id       VARCHAR(64)  NOT NULL,
    behavior_type TINYINT      NOT NULL,
    user_geohash  VARCHAR(128) NULL,
    item_category VARCHAR(64)  NULL,
    `time`        BIGINT       NOT NULL,
    PRIMARY KEY (id),
    KEY idx_user_time (user_id, `time`),
    KEY idx_item_time (item_id, `time`),
    KEY idx_behavior (behavior_type),
    KEY idx_category (item_category)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS tianchi_mobile_recommend_train_item (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    item_id       VARCHAR(64)  NOT NULL,
    item_geohash  VARCHAR(128) NULL,
    item_category VARCHAR(64)  NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_item (item_id),
    KEY idx_category (item_category)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- =============== 涓氬姟琛?===============
CREATE TABLE IF NOT EXISTS biz_user (
    id               BIGINT       NOT NULL AUTO_INCREMENT,
    user_id          VARCHAR(64)  NOT NULL,
    username         VARCHAR(64)  NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    nickname         VARCHAR(64)  NULL,
    avatar_url       VARCHAR(512) NULL,
    phone            VARCHAR(32)  NULL,
    email            VARCHAR(128) NULL,
    gender           TINYINT      NOT NULL DEFAULT 0,
    age_level        VARCHAR(32)  NULL,
    default_geohash  VARCHAR(128) NULL,
    user_type        TINYINT      NOT NULL DEFAULT 1,
    status           TINYINT      NOT NULL DEFAULT 1,
    last_login_at    DATETIME     NULL,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_biz_user_user_id (user_id),
    UNIQUE KEY uk_biz_user_username (username),
    UNIQUE KEY uk_biz_user_phone (phone),
    UNIQUE KEY uk_biz_user_email (email),
    KEY idx_biz_user_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS biz_role (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    role_code  VARCHAR(32)  NOT NULL,
    role_name  VARCHAR(64)  NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_role_code (role_code)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS biz_user_role (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    user_id    VARCHAR(64)  NOT NULL,
    role_code  VARCHAR(32)  NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_biz_user_role_user (user_id, role_code),
    KEY idx_biz_user_role_role (role_code)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS biz_user_login_log (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     VARCHAR(64)  NULL,
    username    VARCHAR(64)  NOT NULL,
    login_type  VARCHAR(32)  NOT NULL DEFAULT 'password',
    client_ip   VARCHAR(64)  NULL,
    user_agent  VARCHAR(512) NULL,
    success     TINYINT      NOT NULL DEFAULT 0,
    fail_reason VARCHAR(255) NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_login_user_time (user_id, created_at),
    KEY idx_login_username_time (username, created_at),
    KEY idx_login_success (success)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS biz_item (
    id            BIGINT        NOT NULL AUTO_INCREMENT,
    item_id       VARCHAR(64)   NOT NULL,
    title         VARCHAR(255)  NOT NULL,
    item_category VARCHAR(64)   NULL,
    item_geohash  VARCHAR(128)  NULL,
    brand         VARCHAR(64)   NULL,
    style_tags    VARCHAR(512)  NULL,
    price_bucket  VARCHAR(32)   NULL,
    price         DECIMAL(10,2) NULL,
    image_url     VARCHAR(512)  NULL,
    status        TINYINT       NOT NULL DEFAULT 1,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_biz_item_item_id (item_id),
    KEY idx_title (title),
    KEY idx_category (item_category),
    KEY idx_brand (brand),
    KEY idx_price_bucket (price_bucket),
    KEY idx_status (status),
    KEY idx_item_category_status (item_category, status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS biz_order_mock (
    id         BIGINT        NOT NULL AUTO_INCREMENT,
    order_id   VARCHAR(64)   NOT NULL,
    user_id    VARCHAR(64)   NOT NULL,
    item_id    VARCHAR(64)   NOT NULL,
    amount     DECIMAL(10,2) NULL,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_order_id (order_id),
    KEY idx_user (user_id),
    KEY idx_item (item_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- =============== 鎺ㄨ崘绯荤粺琛?===============
CREATE TABLE IF NOT EXISTS rec_behavior_log (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    user_id       VARCHAR(64)  NOT NULL,
    item_id       VARCHAR(64)  NOT NULL,
    behavior_type TINYINT      NOT NULL,
    timestamp     BIGINT       NOT NULL,
    request_id    VARCHAR(64)  NULL,
    scene         VARCHAR(32)  NULL,
    source        VARCHAR(32)  NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_behavior_user_time (user_id, timestamp),
    KEY idx_behavior_item_time (item_id, timestamp),
    KEY idx_behavior_type_time (behavior_type, timestamp),
    KEY idx_request (request_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS rec_request_snapshot (
    id             BIGINT       NOT NULL AUTO_INCREMENT,
    request_id     VARCHAR(64)  NOT NULL,
    user_id        VARCHAR(64)  NOT NULL,
    scene          VARCHAR(32)  NULL,
    trigger_type   VARCHAR(32)  NULL,
    item_ids_json  MEDIUMTEXT   NULL,
    model_version  VARCHAR(64)  NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_request_id (request_id),
    KEY idx_request_user (user_id, created_at),
    KEY idx_trigger (trigger_type),
    KEY idx_model (model_version)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS rec_model_version (
    id                        BIGINT       NOT NULL AUTO_INCREMENT,
    model_version             VARCHAR(64)  NOT NULL,
    recall_model_path         VARCHAR(512) NULL,
    ranking_model_path        VARCHAR(512) NULL,
    feature_config_path       VARCHAR(512) NULL,
    user_embedding_path       VARCHAR(512) NULL,
    item_embedding_collection VARCHAR(128) NULL,
    status                    TINYINT      NOT NULL DEFAULT 0,
    trained_at                DATETIME     NULL,
    published_at              DATETIME     NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_model_version (model_version),
    KEY idx_model_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS rec_item_popularity (
    id               BIGINT      NOT NULL AUTO_INCREMENT,
    item_id          VARCHAR(64) NOT NULL,
    exposure_cnt_7d  BIGINT      NOT NULL DEFAULT 0,
    click_cnt_7d     BIGINT      NOT NULL DEFAULT 0,
    cart_cnt_7d      BIGINT      NOT NULL DEFAULT 0,
    purchase_cnt_7d  BIGINT      NOT NULL DEFAULT 0,
    score            DOUBLE      NOT NULL DEFAULT 0,
    stat_time        DATETIME    NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_pop_item (item_id),
    KEY idx_pop_score (score)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS rec_item_tag (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    item_id    VARCHAR(64)  NOT NULL,
    tag_type   VARCHAR(64)  NOT NULL,
    tag_value  VARCHAR(128) NOT NULL,
    weight     DOUBLE       NOT NULL DEFAULT 1.0,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_item_tag (item_id, tag_type, tag_value),
    KEY idx_item_tag (tag_type, tag_value)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS rec_user_tag_preference (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    user_id       VARCHAR(64)  NOT NULL,
    tag_type      VARCHAR(64)  NOT NULL,
    tag_value     VARCHAR(128) NOT NULL,
    score         DOUBLE       NOT NULL DEFAULT 0,
    feature_time  BIGINT       NOT NULL DEFAULT 0,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_user_tag_user (user_id),
    KEY idx_user_tag (user_id, tag_type, tag_value),
    KEY idx_user_tag_score (score)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS rec_lbs_item_index (
    id             BIGINT       NOT NULL AUTO_INCREMENT,
    geohash_prefix VARCHAR(16)  NOT NULL,
    item_id        VARCHAR(64)  NOT NULL,
    item_category  VARCHAR(64)  NULL,
    score          DOUBLE       NOT NULL DEFAULT 0,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_lbs_geo (geohash_prefix),
    KEY idx_lbs_item (item_id),
    KEY idx_lbs_geo_category (geohash_prefix, item_category)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
