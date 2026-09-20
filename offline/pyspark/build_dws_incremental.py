from pyspark.sql.functions import col, count, countDistinct, max as spark_max, sum

from spark_common import create_spark
from watermark import get_watermark, set_watermark


PIPELINE_NAME = "dws.behavior_event"


def build_incremental_item_stats(behavior):
    return (
        behavior.groupBy("item_id")
        .agg(
            count("*").alias("expose_cnt"),
            sum("label").alias("click_cnt"),
            countDistinct("user_id").alias("distinct_user_cnt"),
            spark_max("event_time").alias("last_event_time"),
        )
        .withColumn("ctr", col("click_cnt") / col("expose_cnt"))
    )


def build_incremental_user_stats(behavior):
    return behavior.groupBy("user_id").agg(
        count("*").alias("expose_cnt"),
        sum("label").alias("click_cnt"),
        countDistinct("item_id").alias("distinct_item_cnt"),
        spark_max("event_time").alias("last_event_time"),
    )


def main() -> None:
    spark = create_spark("build_dws_incremental")
    watermark = get_watermark(PIPELINE_NAME)
    new_behavior = spark.table("iceberg.dwd.behavior_event").filter(
        col("event_time") > watermark
    )
    new_count = new_behavior.count()

    if new_count > 0:
        incremental_items = build_incremental_item_stats(new_behavior)
        incremental_users = build_incremental_user_stats(new_behavior)
        incremental_items.createOrReplaceTempView("incremental_item_stat")
        incremental_users.createOrReplaceTempView("incremental_user_stat")

        if spark.catalog.tableExists("iceberg.dws.item_stat"):
            spark.sql("""
                MERGE INTO iceberg.dws.item_stat t
                USING incremental_item_stat s
                ON t.item_id = s.item_id
                WHEN MATCHED THEN UPDATE SET
                    t.expose_cnt = t.expose_cnt + s.expose_cnt,
                    t.click_cnt = t.click_cnt + s.click_cnt,
                    t.distinct_user_cnt = t.distinct_user_cnt + s.distinct_user_cnt,
                    t.last_event_time = greatest(t.last_event_time, s.last_event_time),
                    t.ctr = (t.click_cnt + s.click_cnt) / (t.expose_cnt + s.expose_cnt)
                WHEN NOT MATCHED THEN INSERT
                    (item_id, expose_cnt, click_cnt, distinct_user_cnt, last_event_time, ctr)
                VALUES
                    (s.item_id, s.expose_cnt, s.click_cnt, s.distinct_user_cnt,
                     s.last_event_time, s.ctr)
            """)
        else:
            incremental_items.writeTo("iceberg.dws.item_stat").createOrReplace()

        if spark.catalog.tableExists("iceberg.dws.user_stat"):
            spark.sql("""
                MERGE INTO iceberg.dws.user_stat t
                USING incremental_user_stat s
                ON t.user_id = s.user_id
                WHEN MATCHED THEN UPDATE SET
                    t.expose_cnt = t.expose_cnt + s.expose_cnt,
                    t.click_cnt = t.click_cnt + s.click_cnt,
                    t.distinct_item_cnt = greatest(t.distinct_item_cnt, s.distinct_item_cnt),
                    t.last_event_time = greatest(t.last_event_time, s.last_event_time)
                WHEN NOT MATCHED THEN INSERT
                    (user_id, expose_cnt, click_cnt, distinct_item_cnt, last_event_time)
                VALUES
                    (s.user_id, s.expose_cnt, s.click_cnt,
                     s.distinct_item_cnt, s.last_event_time)
            """)
        else:
            incremental_users.writeTo("iceberg.dws.user_stat").createOrReplace()

        (
            spark.table("iceberg.dws.item_stat")
            .orderBy(col("click_cnt").desc(), col("expose_cnt").desc())
            .limit(5000)
            .writeTo("iceberg.dws.hot_items")
            .createOrReplace()
        )
        max_event_time = new_behavior.agg(spark_max("event_time")).collect()[0][0]
        set_watermark(PIPELINE_NAME, int(max_event_time))

    print(f"dws_incremental_rows={new_count}")
    print(f"dws_watermark={get_watermark(PIPELINE_NAME)}")
    spark.stop()


if __name__ == "__main__":
    main()
