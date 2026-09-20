from pyspark.sql.functions import col, count, countDistinct, max, sum

from spark_common import create_spark


def main() -> None:
    spark = create_spark("build_dws")
    behavior = spark.table("iceberg.dwd.behavior_event")

    item_stat = behavior.groupBy("item_id").agg(
        count("*").alias("expose_cnt"),
        sum("label").alias("click_cnt"),
        countDistinct("user_id").alias("distinct_user_cnt"),
        max("event_time").alias("last_event_time"),
    ).withColumn("ctr", col("click_cnt") / col("expose_cnt"))

    user_stat = behavior.groupBy("user_id").agg(
        count("*").alias("expose_cnt"),
        sum("label").alias("click_cnt"),
        countDistinct("item_id").alias("distinct_item_cnt"),
        max("event_time").alias("last_event_time"),
    )

    hot_items = item_stat.orderBy(
        col("click_cnt").desc(),
        col("expose_cnt").desc(),
    ).limit(5000)

    item_stat.writeTo("iceberg.dws.item_stat").createOrReplace()
    user_stat.writeTo("iceberg.dws.user_stat").createOrReplace()
    hot_items.writeTo("iceberg.dws.hot_items").createOrReplace()

    for table in [
        "iceberg.dws.item_stat",
        "iceberg.dws.user_stat",
        "iceberg.dws.hot_items",
    ]:
        print(table, spark.table(table).count())

    spark.stop()


if __name__ == "__main__":
    main()
