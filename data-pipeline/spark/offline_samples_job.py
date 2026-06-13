"""Spark job: 浠?rec_behavior_log 鏋勯€犲彫鍥?+ 鎺掑簭璁粌鏍锋湰.

鏁版嵁鏉ユ簮鏄ぉ姹?闃块噷绉诲姩鎺ㄨ崘绠楁硶"鏁版嵁闆? 瀛楁鏄犲皠:
    behavior_type 1 = 娴忚/鐐瑰嚮 (CTR 姝ｆ牱鏈?
    behavior_type 2 = 鏀惰棌       (鍙洖姝ｆ牱鏈?
    behavior_type 3 = 鍔犺喘鐗╄溅   (鍙洖姝ｆ牱鏈?
    behavior_type 4 = 璐拱       (CTR + CVR 姝ｆ牱鏈?
    behavior_type 0 = 鏇濆厜       涓嶅瓨鍦?(璇ユ暟鎹泦鏈噰闆嗘洕鍏?

鍥犳 ranking CTR 鐨?鏇濆厜鏈偣鍑?璐熸牱鏈棤娉曚粠绂荤嚎鏁版嵁鑾峰緱, 杩欓噷鐢?"鐢ㄦ埛鏈氦浜掕繃鐨勫晢鍝佹寜鐑害璐熼噰鏍?浠ｆ浛; CVR 璐熸牱鏈垯浣跨敤"宸茬偣鍑绘湭璐拱".

杈撳嚭 Parquet 鍒?data/processed:
  - recall_samples/    (user_id, item_id, label, feature_time, timestamp)
  - ranking_samples/   (user_id, item_id, ctr_label, cvr_label, feature_time, timestamp)

Time Split 绾︽潫:
    feature_time = label_time - 1ms, 璁粌鍓嶄細鏍￠獙 feature_time < label_time.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from algorithm.common.config_loader import get_config


POSITIVE_BEHAVIORS_RECALL = [1, 2, 3, 4]
POSITIVE_BEHAVIOR_CTR = [1, 4]   # 鐐瑰嚮 + 璐拱 瑙嗕负 CTR 姝ｆ牱鏈?POSITIVE_BEHAVIOR_CVR = [4]      # 璐拱 瑙嗕负 CVR 姝ｆ牱鏈?DEFAULT_MAX_BEHAVIOR_ROWS = 10_000_000


def build_jdbc(cfg) -> tuple[str, dict]:
    m = cfg["mysql"]
    url = (f"jdbc:mysql://{m['host']}:{m['port']}/{m['database']}"
           "?useSSL=false&serverTimezone=Asia/Shanghai")
    props = {"user": m["username"], "password": m["password"],
             "driver": "com.mysql.cj.jdbc.Driver"}
    return url, props


def main() -> None:
    cfg = get_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_BEHAVIOR_ROWS,
                        help="rec_behavior_log 鎶芥牱琛屾暟涓婇檺")
    parser.add_argument("--negative-ratio", type=float, default=1.0,
                        help="鍙洖璐熸牱鏈笌姝ｆ牱鏈殑姣斾緥")
    args = parser.parse_args()

    out_dir = Path(cfg["path"]["processedDataDir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    spark = (SparkSession.builder
             .appName("end_to_end_recommendation_system_x_offline_samples")
             .config("spark.sql.session.timeZone", "Asia/Shanghai")
             .getOrCreate())

    jdbc, props = build_jdbc(cfg)
    behavior_all = spark.read.jdbc(jdbc, "rec_behavior_log", properties=props) \
        .select("user_id", "item_id", "behavior_type", "timestamp")

    total = behavior_all.count()
    if total > args.max_rows:
        # 鎸夎閲囨牱鍒?max_rows; 淇濈暀鍏ㄥ瓧娈?        ratio = args.max_rows / total
        behavior = behavior_all.sample(False, ratio, seed=42).limit(args.max_rows)
        print(f"[sample] sampled {args.max_rows:,} from {total:,}")
    else:
        behavior = behavior_all
        print(f"[sample] using all {total:,} rows")
    behavior.cache()

    # ---------------- 鍙洖鏍锋湰 ----------------
    positives = (behavior
                 .filter(F.col("behavior_type").isin(POSITIVE_BEHAVIORS_RECALL))
                 .select("user_id", "item_id", "timestamp")
                 .withColumn("label", F.lit(1))
                 .withColumn("feature_time", F.col("timestamp") - 1))

    # 鍏ㄥ眬鐑棬鍟嗗搧姹犱綔涓鸿礋鏍锋湰鍊欓€? 姣旂畝鍗?random 鏇存帴杩?妯″瀷鍙兘鍙洖浣嗙敤鎴锋病鐪?鐨勫垎甯?    item_pool_df = (behavior.groupBy("item_id").count()
                    .orderBy(F.desc("count"))
                    .limit(50_000))
    item_pool = [r["item_id"] for r in item_pool_df.collect()]
    print(f"[sample] item_pool size for negative sampling: {len(item_pool)}")

    if item_pool:
        @F.udf("string")
        def rand_item(_):
            import random
            return random.choice(item_pool)

        n_neg = int(positives.count() * args.negative_ratio)
        negatives = (positives
                     .sample(False, min(1.0, args.negative_ratio), seed=7)
                     .withColumn("item_id", rand_item(F.col("user_id")))
                     .withColumn("label", F.lit(0)))
        recall = positives.unionByName(negatives, allowMissingColumns=True)
    else:
        recall = positives
    recall.write.mode("overwrite").parquet(str(out_dir / "recall_samples"))
    print(f"[recall] wrote samples -> {out_dir/'recall_samples'}")

    # ---------------- 鎺掑簭鏍锋湰 ----------------
    # CTR 姝ｆ牱鏈? behavior_type in (1,4); CVR 姝ｆ牱鏈? behavior_type=4
    # CTR 璐熸牱鏈? 浠?item_pool 鎶芥牱, 涓?(user_id) 褰㈡垚"鏈氦浜?浼洕鍏?    # CVR 璐熸牱鏈? 鐐瑰嚮 (b=1) 浣嗗悓鐢ㄦ埛/鍚岀獥鍙ｅ唴娌℃湁 b=4 璐拱
    ctr_pos = (behavior
               .filter(F.col("behavior_type").isin(POSITIVE_BEHAVIOR_CTR))
               .select("user_id", "item_id", "timestamp")
               .withColumn("ctr_label", F.lit(1))
               .withColumn("cvr_label",
                           F.when(F.col("timestamp").isNotNull(), F.lit(0)).otherwise(F.lit(0))))

    # 璐拱琛屼负瀵瑰簲 cvr_label=1; 鍏朵綑 ctr_pos 琛?cvr_label=0
    purchases = (behavior
                 .filter(F.col("behavior_type") == 4)
                 .select("user_id", "item_id")
                 .withColumn("is_buy", F.lit(1))
                 .dropDuplicates(["user_id", "item_id"]))
    ctr_pos = (ctr_pos.join(purchases, ["user_id", "item_id"], "left")
               .withColumn("cvr_label", F.coalesce(F.col("is_buy"), F.lit(0)))
               .drop("is_buy"))

    if item_pool:
        @F.udf("string")
        def rand_item2(_):
            import random
            return random.choice(item_pool)
        ctr_neg = (ctr_pos
                   .sample(False, min(1.0, args.negative_ratio), seed=11)
                   .withColumn("item_id", rand_item2(F.col("user_id")))
                   .withColumn("ctr_label", F.lit(0))
                   .withColumn("cvr_label", F.lit(0)))
        ranking = ctr_pos.unionByName(ctr_neg, allowMissingColumns=True)
    else:
        ranking = ctr_pos

    ranking = ranking.withColumn("feature_time", F.col("timestamp") - 1)
    ranking.write.mode("overwrite").parquet(str(out_dir / "ranking_samples"))
    print(f"[ranking] wrote samples -> {out_dir/'ranking_samples'}")

    spark.stop()


if __name__ == "__main__":
    main()
