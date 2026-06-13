-- Seed roles and admin user.
USE end_to_end_recommendation_system_x;

INSERT IGNORE INTO biz_role (role_code, role_name) VALUES
    ('USER',  '鏅€氱敤鎴?),
    ('ADMIN', '绠＄悊鍛?);

-- Admin user is NOT seeded here because BCrypt hashes must be generated at install time.
-- Use scripts/bootstrap_admin.py (or call /auth/register then promote via /admin/users/{id}/roles).

-- Sample items for first-run smoke testing (real data should be imported from raw csv).
INSERT IGNORE INTO biz_item
    (item_id, title, item_category, brand, style_tags, price_bucket, price, image_url, status)
VALUES
    ('10001', '娼祦杩愬姩闉?,   '300', 'nike',   'street',   '100_300',  399.00, 'http://localhost:8080/static/item/10001.jpg', 1),
    ('10002', '澶嶅彜鍗。',     '301', 'adidas', 'vintage',  '100_300',  259.00, 'http://localhost:8080/static/item/10002.jpg', 1),
    ('10003', '鏈鸿兘鍙岃偐鍖?,   '302', 'nike',   'tech',     '300_500',  459.00, 'http://localhost:8080/static/item/10003.jpg', 1),
    ('10004', '鍩虹鐧絋',      '303', 'uniqlo', 'basic',    '0_100',     99.00, 'http://localhost:8080/static/item/10004.jpg', 1),
    ('10005', '杩愬姩鐭￥',     '300', 'nike',   'sport',    '100_300',  199.00, 'http://localhost:8080/static/item/10005.jpg', 1),
    ('10006', '琛楀ご宸ヨ瑁?,   '301', 'carhartt','street',  '300_500',  499.00, 'http://localhost:8080/static/item/10006.jpg', 1),
    ('10007', '閫氬嫟鍏枃鍖?,   '304', 'tumi',   'business', '500_plus', 899.00, 'http://localhost:8080/static/item/10007.jpg', 1),
    ('10008', '浼戦棽甯嗗竷闉?,   '300', 'vans',   'casual',   '100_300',  329.00, 'http://localhost:8080/static/item/10008.jpg', 1);

INSERT IGNORE INTO rec_item_popularity (item_id, exposure_cnt_7d, click_cnt_7d, cart_cnt_7d, purchase_cnt_7d, score, stat_time) VALUES
    ('10001', 1000, 200, 30, 8, 0.92, NOW()),
    ('10002',  900, 180, 25, 6, 0.85, NOW()),
    ('10003',  800, 160, 22, 5, 0.78, NOW()),
    ('10004',  700, 140, 18, 4, 0.71, NOW()),
    ('10005',  600, 120, 15, 3, 0.65, NOW()),
    ('10006',  500, 100, 10, 2, 0.55, NOW()),
    ('10007',  400,  80,  8, 1, 0.45, NOW()),
    ('10008',  300,  60,  5, 1, 0.35, NOW());

INSERT IGNORE INTO rec_item_tag (item_id, tag_type, tag_value, weight) VALUES
    ('10001', 'item_category', '300',     1.0), ('10001', 'brand', 'nike',     1.0), ('10001', 'price_bucket', '100_300', 1.0),
    ('10002', 'item_category', '301',     1.0), ('10002', 'brand', 'adidas',   1.0), ('10002', 'price_bucket', '100_300', 1.0),
    ('10003', 'item_category', '302',     1.0), ('10003', 'brand', 'nike',     1.0), ('10003', 'price_bucket', '300_500', 1.0),
    ('10004', 'item_category', '303',     1.0), ('10004', 'brand', 'uniqlo',   1.0), ('10004', 'price_bucket', '0_100',   1.0),
    ('10005', 'item_category', '300',     1.0), ('10005', 'brand', 'nike',     1.0), ('10005', 'price_bucket', '100_300', 1.0),
    ('10006', 'item_category', '301',     1.0), ('10006', 'brand', 'carhartt', 1.0), ('10006', 'price_bucket', '300_500', 1.0),
    ('10007', 'item_category', '304',     1.0), ('10007', 'brand', 'tumi',     1.0), ('10007', 'price_bucket', '500_plus',1.0),
    ('10008', 'item_category', '300',     1.0), ('10008', 'brand', 'vans',     1.0), ('10008', 'price_bucket', '100_300', 1.0);

INSERT IGNORE INTO rec_model_version
    (model_version, recall_model_path, ranking_model_path, feature_config_path, user_embedding_path, item_embedding_collection, status, trained_at, published_at)
VALUES
    ('20260526_0000',
     'E:/End-To-End_Recommendation_System_X/data/model/recall_user_tower.pt',
     'E:/End-To-End_Recommendation_System_X/data/model/ranking_mmoe.pt',
     'E:/End-To-End_Recommendation_System_X/data/model/feature_config.json',
     'E:/End-To-End_Recommendation_System_X/data/model/user_embedding_table.pt',
     'item_embedding', 1, NOW(), NOW());
