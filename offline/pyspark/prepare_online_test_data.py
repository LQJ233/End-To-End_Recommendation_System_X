import json
from pathlib import Path

import redis
from pyspark.sql import Window
from pyspark.sql.functions import col, count, countDistinct, desc, row_number

from spark_common import create_spark


OUTPUT_FILE = Path(
    "/Users/qj/Item/End-To-End_Recommendation_System_X/offline/training_output/"
    "online_test_users.json"
)


def select_test_users(
    behavior,
    min_clicks: int = 10,
    min_distinct_items: int = 5,
    min_exposures: int = 50,
    limit: int = 20,
):
    click_stats = (
        behavior.filter(col("label") == 1)
        .groupBy("user_id")
        .agg(
            count("*").alias("click_cnt"),
            countDistinct("item_id").alias("distinct_item_cnt"),
        )
    )
    expose_stats = (
        behavior.filter(col("label") == 0)
        .groupBy("user_id")
        .agg(count("*").alias("expose_cnt"))
    )
    return (
        click_stats.join(expose_stats, on="user_id", how="left")
        .fillna({"expose_cnt": 0})
        .filter(
            (col("click_cnt") >= min_clicks)
            & (col("distinct_item_cnt") >= min_distinct_items)
            & (col("expose_cnt") >= min_exposures)
        )
        .orderBy(desc("click_cnt"), desc("expose_cnt"))
        .limit(limit)
    )


def main() -> None:
    spark = create_spark("prepare_online_test_data")
    behavior = spark.table("iceberg.dwd.behavior_event")

    selected_users = select_test_users(behavior)
    user_rows = selected_users.collect()
    selected_user_ids = [row.user_id for row in user_rows]

    window = Window.partitionBy("user_id").orderBy(desc("event_time"))
    history_rows = (
        behavior.filter(col("label") == 1)
        .filter(col("user_id").isin(selected_user_ids))
        .withColumn("row_number", row_number().over(window))
        .filter(col("row_number") <= 20)
        .select("user_id", "item_id")
        .collect()
    )

    history_by_user: dict[int, list[int]] = {}
    for row in history_rows:
        history_by_user.setdefault(int(row.user_id), []).append(int(row.item_id))

    redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    summary = []
    for user_row in user_rows:
        user_id = int(user_row.user_id)
        history = history_by_user.get(user_id, [])
        history_key = f"adrec:user:history:{user_id}"
        feature_key = f"adrec:user:features:{user_id}"
        redis_client.delete(history_key, feature_key)
        if history:
            redis_client.rpush(history_key, *[str(item_id) for item_id in history])
        redis_client.hset(
            feature_key,
            mapping={
                "click_count": int(user_row.click_cnt),
                "distinct_item_count": int(user_row.distinct_item_cnt),
                "expose_count": int(user_row.expose_cnt),
            },
        )
        summary.append(
            {
                "user_id": user_id,
                "click_count": int(user_row.click_cnt),
                "distinct_item_count": int(user_row.distinct_item_cnt),
                "expose_count": int(user_row.expose_cnt),
                "history_items": history,
            }
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"prepared_users={len(summary)}")
    print(f"output={OUTPUT_FILE}")
    spark.stop()


if __name__ == "__main__":
    main()
