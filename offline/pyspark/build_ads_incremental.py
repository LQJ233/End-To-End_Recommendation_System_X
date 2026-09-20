from pyspark.sql.functions import broadcast, col, max as spark_max

from spark_common import create_spark
from watermark import get_watermark, set_watermark


PIPELINE_NAME = "ads.training_sample"


def build_incremental_sample(behavior, item, user):
    return (
        behavior.alias("b")
        .join(
            broadcast(item.alias("i")),
            col("b.item_id") == col("i.item_id"),
            "left",
        )
        .join(
            broadcast(user.alias("u")),
            col("b.user_id") == col("u.user_id"),
            "left",
        )
        .select(
            col("b.label"),
            col("b.user_id"),
            col("b.item_id"),
            col("b.event_time"),
            col("i.category_id"),
            col("i.brand_id"),
            col("i.price"),
            col("i.campaign_id"),
            col("i.customer_id"),
            col("u.cms_segid"),
            col("u.cms_group_id"),
            col("u.final_gender_code"),
            col("u.age_level"),
            col("u.pvalue_level"),
            col("u.shopping_level"),
            col("u.occupation"),
            col("u.new_user_class_level"),
        )
    )


def main() -> None:
    spark = create_spark("build_ads_incremental")
    watermark = get_watermark(PIPELINE_NAME)
    new_behavior = spark.table("iceberg.dwd.behavior_event").filter(
        col("event_time") > watermark
    )
    new_count = new_behavior.count()

    if new_count > 0:
        sample = build_incremental_sample(
            new_behavior,
            spark.table("iceberg.dwd.item"),
            spark.table("iceberg.dwd.user"),
        )
        sample.writeTo("iceberg.ads.training_sample").append()
        max_event_time = new_behavior.agg(spark_max("event_time")).collect()[0][0]
        set_watermark(PIPELINE_NAME, int(max_event_time))

    print(f"ads_incremental_rows={new_count}")
    print(f"ads_watermark={get_watermark(PIPELINE_NAME)}")
    spark.stop()


if __name__ == "__main__":
    main()
