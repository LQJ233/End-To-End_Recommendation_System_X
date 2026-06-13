"""Spark job: rebuild rec_item_popularity and Redis rec:hot:items ZSet."""
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

    spark = SparkSession.builder.appName("end_to_end_recommendation_system_x_popularity").getOrCreate()
    behavior = spark.read.jdbc(jdbc, "rec_behavior_log", properties=props)
    cutoff = F.unix_timestamp() * 1000 - 7 * 86400 * 1000
    recent = behavior.filter(F.col("timestamp") >= cutoff)

    agg = (recent.groupBy("item_id").agg(
        F.sum(F.when(F.col("behavior_type") == 0, 1).otherwise(0)).alias("exposure_cnt_7d"),
        F.sum(F.when(F.col("behavior_type") == 1, 1).otherwise(0)).alias("click_cnt_7d"),
        F.sum(F.when(F.col("behavior_type") == 3, 1).otherwise(0)).alias("cart_cnt_7d"),
        F.sum(F.when(F.col("behavior_type") == 4, 1).otherwise(0)).alias("purchase_cnt_7d"),
    ).withColumn("score",
                 F.col("click_cnt_7d") * 1.0
                 + F.col("cart_cnt_7d") * 3.0
                 + F.col("purchase_cnt_7d") * 5.0))

    # truncate=true preserves the table schema + indexes when overwriting.
    write_props = dict(props); write_props["truncate"] = "true"
    agg.withColumn("stat_time", F.current_timestamp()) \
        .write.mode("overwrite").jdbc(jdbc, "rec_item_popularity", properties=write_props)

    r_cfg = cfg["redis"]
    r = redis.Redis(host=r_cfg["host"], port=int(r_cfg["port"]),
                    db=int(r_cfg.get("database", 0)),
                    password=r_cfg.get("password") or None, decode_responses=True)
    r.delete("rec:hot:items")
    rows = agg.orderBy(F.desc("score")).limit(int(cfg["fallback"]["hotItemSize"])).collect()
    if rows:
        mapping = {row["item_id"]: float(row["score"]) for row in rows}
        r.zadd("rec:hot:items", mapping)
        r.expire("rec:hot:items", 86400)
    spark.stop()


if __name__ == "__main__":
    main()
