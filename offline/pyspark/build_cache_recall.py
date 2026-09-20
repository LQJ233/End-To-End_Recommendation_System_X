import redis
from pyspark.sql import Window
from pyspark.sql.functions import col, count, desc, row_number

from spark_common import create_spark


def build_cache_candidates(
    clicks,
    item_features,
    item_scores,
    max_categories: int = 3,
    limit: int = 50,
    min_clicks: int = 5,
    max_items_per_category: int = 200,
):
    click_events = clicks.filter(col("label") == 1)
    user_click_count = click_events.groupBy("user_id").agg(count("*").alias("user_click_cnt"))
    active_users = user_click_count.filter(col("user_click_cnt") >= min_clicks)

    item_category = item_features.select("item_id", "category_id")
    user_category = (
        click_events.select("user_id", "item_id")
        .join(item_category, on="item_id", how="inner")
        .groupBy("user_id", "category_id")
        .agg(count("*").alias("category_click_cnt"))
    )
    category_window = Window.partitionBy("user_id").orderBy(
        desc("category_click_cnt"),
        desc("category_id"),
    )
    top_categories = (
        user_category.withColumn("category_rank", row_number().over(category_window))
        .filter(col("category_rank") <= max_categories)
    )

    scored_items = (
        item_scores.select("item_id", "click_cnt", "ctr")
        .join(item_category, on="item_id", how="inner")
        .withColumn(
            "score",
            col("click_cnt").cast("double") + col("ctr").cast("double"),
        )
    )
    item_window = Window.partitionBy("category_id").orderBy(
        desc("score"),
        desc("click_cnt"),
        desc("item_id"),
    )
    scored_items = (
        scored_items.withColumn("item_rank", row_number().over(item_window))
        .filter(col("item_rank") <= max_items_per_category)
        .drop("item_rank")
    )
    clicked_items = click_events.select("user_id", "item_id")
    candidates = (
        active_users.select("user_id")
        .join(top_categories, on="user_id", how="inner")
        .join(scored_items, on="category_id", how="inner")
        .join(clicked_items, on=["user_id", "item_id"], how="left_anti")
        .withColumn(
            "score",
            col("score"),
        )
    )

    candidate_window = Window.partitionBy("user_id").orderBy(
        desc("score"),
        desc("click_cnt"),
        desc("item_id"),
    )
    return (
        candidates.withColumn("candidate_rank", row_number().over(candidate_window))
        .filter(col("candidate_rank") <= limit)
        .select("user_id", "item_id", "score")
    )


def main() -> None:
    spark = create_spark("build_cache_recall")
    clicks = spark.table("iceberg.dwd.behavior_event")
    item_features = spark.table("iceberg.dwd.item")
    item_scores = spark.table("iceberg.dws.item_stat")

    candidates = build_cache_candidates(clicks, item_features, item_scores)
    rows = candidates.collect()

    redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    by_user: dict[int, list[str]] = {}
    for row in rows:
        by_user.setdefault(int(row.user_id), []).append(str(int(row.item_id)))

    for user_id, item_ids in by_user.items():
        key = f"adrec:recall:cache:{user_id}"
        redis_client.delete(key)
        if item_ids:
            redis_client.rpush(key, *item_ids)

    print(f"cache_recall_users={len(by_user)}")
    print(f"cache_recall_rows={len(rows)}")
    spark.stop()


if __name__ == "__main__":
    main()
