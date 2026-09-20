CREATE TABLE IF NOT EXISTS item_datax_sync (
    id BIGINT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category_id BIGINT NOT NULL,
    brand_id BIGINT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500) NULL,
    status TINYINT NOT NULL
);
