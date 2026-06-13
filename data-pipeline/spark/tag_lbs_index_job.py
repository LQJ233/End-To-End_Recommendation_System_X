"""Spark job: rebuild Redis tag/LBS inverted indices from biz_item + rec_item_tag."""
from __future__ import annotations

import sys
from pathlib import Path

import redis
from pyspark.sql import SparkSession, functions as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from algorithm.common.config_loader import get_config


def main() -> None:
    cfg = get_config()
    m = cfg["mysql"]
    jdbc = f"jdbc:mysql://{m['host']}:{m['port']}/{m['database']}?useSSL=false&serverTimezone=Asia/Shanghai"
    props = {"user": m["username"], "password": m["password"], "driver": "com.mysql.cj.jdbc.Driver"}

    spark = SparkSession.builder.appName("end_to_end_recommendation_system_x_tag_lbs_index").getOrCreate()

    items = spark.read.jdbc(jdbc, "biz_item", properties=props).filter(F.col("status") == 1)
    tags = spark.read.jdbc(jdbc, "rec_item_tag", properties=props)
    popularity = spark.read.jdbc(jdbc, "rec_item_popularity", properties=props).select("item_id", "score")

    tagged = (tags.join(popularity, "item_id", "left")
              .withColumn("final_score", F.coalesce(F.col("score"), F.lit(0.0)) + F.col("weight")))

    r_cfg = cfg["redis"]
    r = redis.Redis(host=r_cfg["host"], port=int(r_cfg["port"]),
                    db=int(r_cfg.get("database", 0)),
                    password=r_cfg.get("password") or None, decode_responses=True)

    # Tag inverted index: rec:tag:index:{tagType}:{tagValue}
    rows = tagged.select("tag_type", "tag_value", "item_id", "final_score").collect()
    keys_seen = set()
    for row in rows:
        key = f"rec:tag:index:{row['tag_type']}:{row['tag_value']}"
        if key not in keys_seen:
            r.delete(key)
            keys_seen.add(key)
        r.zadd(key, {row["item_id"]: float(row["final_score"])})
        r.expire(key, 86400)

    # LBS index: rec:lbs:index:{geohashPrefix}
    prefix_len = int(cfg["recommendation"].get("lbsGeoHashPrefixLength", 5))
    lbs = items.filter(F.col("item_geohash").isNotNull()) \
        .withColumn("prefix", F.substring(F.col("item_geohash"), 1, prefix_len)) \
        .join(popularity, "item_id", "left") \
        .withColumn("final_score", F.coalesce(F.col("score"), F.lit(1.0))) \
        .select("prefix", "item_id", "item_category", "final_score").collect()
    lbs_keys_seen = set()
    for row in lbs:
        key = f"rec:lbs:index:{row['prefix']}"
        if key not in lbs_keys_seen:
            r.delete(key)
            lbs_keys_seen.add(key)
        r.zadd(key, {row["item_id"]: float(row["final_score"])})
        r.expire(key, 86400)

    spark.stop()


if __name__ == "__main__":
    main()
