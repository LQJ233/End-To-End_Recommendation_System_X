from pyspark.sql.functions import coalesce, col, lit, when

from spark_common import create_spark


def build_behavior_event_df(raw_behavior_df):
    return raw_behavior_df.select(
        col("user").alias("user_id"),
        col("adgroup_id").alias("item_id"),
        col("time_stamp").alias("event_time"),
        col("pid").alias("pid"),
        when(col("clk") == 1, "click").otherwise("expose").alias("event_type"),
        col("clk").cast("int").alias("label"),
    )


def build_item_df(ad_feature_df):
    return ad_feature_df.select(
        coalesce(col("adgroup_id"), lit(0)).alias("item_id"),
        coalesce(col("cate_id"), lit(0)).alias("category_id"),
        coalesce(col("campaign_id"), lit(0)).alias("campaign_id"),
        coalesce(col("customer"), lit(0)).alias("customer_id"),
        coalesce(col("brand"), lit(0)).alias("brand_id"),
        coalesce(col("price"), lit(0.0)).alias("price"),
    )


def build_user_df(user_profile_df):
    return user_profile_df.select(
        col("userid").alias("user_id"),
        col("cms_segid").alias("cms_segid"),
        col("cms_group_id").alias("cms_group_id"),
        col("final_gender_code").alias("final_gender_code"),
        col("age_level").alias("age_level"),
        col("pvalue_level").alias("pvalue_level"),
        col("shopping_level").alias("shopping_level"),
        col("occupation").alias("occupation"),
        col("new_user_class_level").alias("new_user_class_level"),
    )


def build_behavior_event(spark) -> None:
    build_behavior_event_df(
        spark.table("iceberg.ods.raw_behavior_sample")
    ).writeTo("iceberg.dwd.behavior_event").createOrReplace()


def build_item(spark) -> None:
    build_item_df(
        spark.table("iceberg.ods.ad_feature")
    ).writeTo("iceberg.dwd.item").createOrReplace()


def build_user(spark) -> None:
    build_user_df(
        spark.table("iceberg.ods.user_profile")
    ).writeTo("iceberg.dwd.user").createOrReplace()


def main() -> None:
    spark = create_spark("build_dwd")
    build_behavior_event(spark)
    build_item(spark)
    build_user(spark)

    for table in [
        "iceberg.dwd.behavior_event",
        "iceberg.dwd.item",
        "iceberg.dwd.user",
    ]:
        print(table, spark.table(table).count())

    spark.stop()


if __name__ == "__main__":
    main()
