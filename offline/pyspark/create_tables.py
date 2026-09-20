from spark_common import create_spark


def main() -> None:
    spark = create_spark("create_iceberg_ods_tables")

    spark.sql("CREATE DATABASE IF NOT EXISTS iceberg.ods")

    spark.sql("""
        CREATE TABLE IF NOT EXISTS iceberg.ods.raw_behavior_sample (
            user BIGINT,
            time_stamp BIGINT,
            adgroup_id BIGINT,
            pid STRING,
            nonclk INT,
            clk INT
        ) USING iceberg
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS iceberg.ods.ad_feature (
            adgroup_id BIGINT,
            cate_id BIGINT,
            campaign_id BIGINT,
            customer BIGINT,
            brand BIGINT,
            price DOUBLE
        ) USING iceberg
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS iceberg.ods.user_profile (
            userid BIGINT,
            cms_segid BIGINT,
            cms_group_id BIGINT,
            final_gender_code BIGINT,
            age_level BIGINT,
            pvalue_level BIGINT,
            shopping_level BIGINT,
            occupation BIGINT,
            new_user_class_level BIGINT
        ) USING iceberg
    """)

    spark.sql("SHOW TABLES IN iceberg.ods").show(truncate=False)
    spark.stop()


if __name__ == "__main__":
    main()
