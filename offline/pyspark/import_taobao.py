from pathlib import Path

from pyspark.sql.functions import col, when

from spark_common import create_spark


DATA_DIR = Path("/Users/qj/Item/End-To-End_Recommendation_System_X/Data")


def load_raw_sample(spark):
    df = spark.read.option("header", True).csv(str(DATA_DIR / "raw_sample.csv"))
    df = df.toDF(*[c.strip() for c in df.columns])
    return (
        df.select(
            col("user").cast("bigint"),
            col("time_stamp").cast("bigint"),
            col("adgroup_id").cast("bigint"),
            col("pid").cast("string"),
            col("nonclk").cast("int"),
            col("clk").cast("int"),
        )
    )


def load_ad_feature(spark):
    df = spark.read.option("header", True).csv(str(DATA_DIR / "ad_feature.csv"))
    df = df.toDF(*[c.strip() for c in df.columns])
    return (
        df.select(
            col("adgroup_id").cast("bigint"),
            col("cate_id").cast("bigint"),
            col("campaign_id").cast("bigint"),
            col("customer").cast("bigint"),
            col("brand").cast("bigint"),
            col("price").cast("double"),
        )
    )


def load_user_profile(spark):
    df = spark.read.option("header", True).csv(str(DATA_DIR / "user_profile.csv"))
    df = df.toDF(*[c.strip() for c in df.columns])
    return (
        df.select(
            col("userid").cast("bigint"),
            col("cms_segid").cast("bigint"),
            col("cms_group_id").cast("bigint"),
            col("final_gender_code").cast("bigint"),
            col("age_level").cast("bigint"),
            col("pvalue_level").cast("bigint"),
            col("shopping_level").cast("bigint"),
            col("occupation").cast("bigint"),
            col("new_user_class_level").cast("bigint"),
        )
    )


def main() -> None:
    spark = create_spark("import_taobao_ad_click")

    raw_df = load_raw_sample(spark)
    ad_df = load_ad_feature(spark)
    user_df = load_user_profile(spark)

    raw_df.writeTo("iceberg.ods.raw_behavior_sample").overwritePartitions()
    ad_df.writeTo("iceberg.ods.ad_feature").overwritePartitions()
    user_df.writeTo("iceberg.ods.user_profile").overwritePartitions()

    print("raw_sample count:", spark.table("iceberg.ods.raw_behavior_sample").count())
    print("ad_feature count:", spark.table("iceberg.ods.ad_feature").count())
    print("user_profile count:", spark.table("iceberg.ods.user_profile").count())

    spark.stop()


if __name__ == "__main__":
    main()
