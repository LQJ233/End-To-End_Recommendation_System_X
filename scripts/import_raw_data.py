"""Import Tianchi Mobile Recommendation CSVs into MySQL.

数据集来源:
    阿里巴巴移动推荐算法 (https://tianchi.aliyun.com/dataset/46)
    - tianchi_mobile_recommend_train_user.csv  ~23M 行 / ~1 GB
    - tianchi_mobile_recommend_train_item.csv  ~620K 行 / ~10 MB

字段说明:
    user csv : user_id, item_id, behavior_type, user_geohash, item_category, time
    item csv : item_id, item_geohash, item_category

行为类型:
    1 = 浏览/点击
    2 = 收藏
    3 = 加购物车
    4 = 购买
    (该数据集不包含 0 = 曝光; 项目的 0 由 Nginx Lua 在线埋点采集.)

时间字段:
    格式为 'YYYY-MM-DD HH' (按小时粒度), 导入时转换为毫秒时间戳.

默认行为:
    user.csv 最多导入 10,000,000 行, 用于本地训练; 可通过 --max-rows 调整.
    item.csv 全量导入 (体量很小).

用法:
    python scripts/import_raw_data.py --max-rows 10000000
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithm.common.config_loader import get_config


DEFAULT_MAX_USER_ROWS = 10_000_000


def connect():
    cfg = get_config()["mysql"]
    return pymysql.connect(
        host=cfg["host"], port=int(cfg["port"]), user=cfg["username"],
        password=cfg["password"], database=cfg["database"], charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=False,
        local_infile=True,
    )


def parse_time(t: str) -> int | None:
    """天池 time 字段是 'yyyy-MM-dd HH' 小时粒度; 也兼容已经是数字的毫秒/秒值."""
    t = (t or "").strip()
    if not t:
        return None
    try:
        return int(datetime.strptime(t, "%Y-%m-%d %H").timestamp() * 1000)
    except ValueError:
        pass
    try:
        v = int(t)
        # 自动判断秒还是毫秒
        return v * 1000 if v < 10_000_000_000 else v
    except ValueError:
        return None


def import_user_csv(conn, csv_path: Path, max_rows: int, batch_size: int = 5000) -> int:
    sql_raw = (
        "INSERT INTO tianchi_mobile_recommend_train_user "
        "(user_id,item_id,behavior_type,user_geohash,item_category,`time`) "
        "VALUES (%s,%s,%s,%s,%s,%s)"
    )
    sql_behavior = (
        "INSERT INTO rec_behavior_log "
        "(user_id,item_id,behavior_type,timestamp,scene,source) "
        "VALUES (%s,%s,%s,%s,'home','import')"
    )
    total = 0
    skipped = 0
    started = time.time()
    batch_raw, batch_b = [], []

    print(f"[user] importing {csv_path} (max_rows={max_rows:,})")
    with conn.cursor() as cur, csv_path.open("r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        header = next(reader, None)
        for row in reader:
            if total >= max_rows:
                print(f"[user] reached max_rows={max_rows:,}, stop")
                break
            if len(row) < 6:
                skipped += 1
                continue
            user_id, item_id, behavior_type, geohash, category, t = row[:6]
            try:
                bt = int(behavior_type)
            except ValueError:
                skipped += 1
                continue
            ts = parse_time(t)
            if ts is None:
                skipped += 1
                continue
            batch_raw.append((user_id, item_id, bt, geohash or None, category or None, ts))
            batch_b.append((user_id, item_id, bt, ts))
            if len(batch_raw) >= batch_size:
                cur.executemany(sql_raw, batch_raw)
                cur.executemany(sql_behavior, batch_b)
                conn.commit()
                total += len(batch_raw)
                batch_raw.clear()
                batch_b.clear()
                if total % 100_000 == 0:
                    elapsed = time.time() - started
                    rate = total / max(elapsed, 1e-6)
                    print(f"[user] inserted {total:,} rows ({rate:,.0f} rows/s, skipped={skipped})")
        if batch_raw:
            cur.executemany(sql_raw, batch_raw)
            cur.executemany(sql_behavior, batch_b)
            conn.commit()
            total += len(batch_raw)
    elapsed = time.time() - started
    print(f"[user] done: total={total:,} skipped={skipped} elapsed={elapsed:,.1f}s")
    return total


def import_item_csv(conn, csv_path: Path, batch_size: int = 5000) -> int:
    sql_raw = (
        "INSERT INTO tianchi_mobile_recommend_train_item "
        "(item_id,item_geohash,item_category) VALUES (%s,%s,%s)"
    )
    # biz_item 用于前端展示, 这里给一些占位字段以满足 schema; 后续可以用更精细的脚本覆盖.
    sql_biz = (
        "INSERT IGNORE INTO biz_item "
        "(item_id,title,item_category,item_geohash,brand,style_tags,price_bucket,price,image_url,status) "
        "VALUES (%s,%s,%s,%s,'unknown','default','0_100',99.00,'',1)"
    )
    total = 0
    skipped = 0
    started = time.time()
    batch_raw, batch_biz = [], []

    print(f"[item] importing {csv_path}")
    with conn.cursor() as cur, csv_path.open("r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        next(reader, None)
        for row in reader:
            if len(row) < 3:
                skipped += 1
                continue
            item_id, geohash, category = row[:3]
            if not item_id:
                skipped += 1
                continue
            batch_raw.append((item_id, geohash or None, category or None))
            batch_biz.append((item_id, f"商品 {item_id}", category or None, geohash or None))
            if len(batch_raw) >= batch_size:
                cur.executemany(sql_raw, batch_raw)
                cur.executemany(sql_biz, batch_biz)
                conn.commit()
                total += len(batch_raw)
                batch_raw.clear()
                batch_biz.clear()
                if total % 100_000 == 0:
                    print(f"[item] inserted {total:,} rows (skipped={skipped})")
        if batch_raw:
            cur.executemany(sql_raw, batch_raw)
            cur.executemany(sql_biz, batch_biz)
            conn.commit()
            total += len(batch_raw)
    elapsed = time.time() - started
    print(f"[item] done: total={total:,} skipped={skipped} elapsed={elapsed:,.1f}s")
    return total


def derive_item_tags(conn) -> None:
    """根据 biz_item 自动补 rec_item_tag(item_category / brand / price_bucket).

    天池原始数据没有 brand / price_bucket, biz_item.brand 是占位 'unknown'.
    这里仍把它写入标签倒排, 让标签召回链路能跑通; 真实场景应替换为实际打标流程.
    """
    sql = (
        "INSERT INTO rec_item_tag (item_id, tag_type, tag_value, weight) "
        "SELECT item_id, 'item_category', item_category, 1.0 FROM biz_item "
        "WHERE item_category IS NOT NULL "
        "ON DUPLICATE KEY UPDATE weight = VALUES(weight)"
    )
    sql_brand = (
        "INSERT INTO rec_item_tag (item_id, tag_type, tag_value, weight) "
        "SELECT item_id, 'brand', brand, 1.0 FROM biz_item "
        "WHERE brand IS NOT NULL AND brand <> '' "
        "ON DUPLICATE KEY UPDATE weight = VALUES(weight)"
    )
    sql_price = (
        "INSERT INTO rec_item_tag (item_id, tag_type, tag_value, weight) "
        "SELECT item_id, 'price_bucket', price_bucket, 1.0 FROM biz_item "
        "WHERE price_bucket IS NOT NULL AND price_bucket <> '' "
        "ON DUPLICATE KEY UPDATE weight = VALUES(weight)"
    )
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(sql_brand)
        cur.execute(sql_price)
        conn.commit()
    print("[tag] rec_item_tag refreshed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_USER_ROWS,
                        help=f"user.csv 导入行数上限 (默认 {DEFAULT_MAX_USER_ROWS:,})")
    parser.add_argument("--raw-dir", default=None,
                        help="原始 csv 目录 (默认读 conf path.rawDataDir)")
    parser.add_argument("--skip-item", action="store_true", help="跳过 item.csv 导入")
    parser.add_argument("--skip-user", action="store_true", help="跳过 user.csv 导入")
    parser.add_argument("--skip-tags", action="store_true", help="跳过 rec_item_tag 派生")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir or get_config()["path"]["rawDataDir"])
    user_csv = raw_dir / "tianchi_mobile_recommend_train_user.csv"
    item_csv = raw_dir / "tianchi_mobile_recommend_train_item.csv"

    conn = connect()
    try:
        if not args.skip_item:
            if item_csv.exists():
                import_item_csv(conn, item_csv)
            else:
                print(f"[item] missing {item_csv}, skipped")
        if not args.skip_user:
            if user_csv.exists():
                import_user_csv(conn, user_csv, max_rows=args.max_rows)
            else:
                print(f"[user] missing {user_csv}, skipped")
        if not args.skip_tags:
            derive_item_tags(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
