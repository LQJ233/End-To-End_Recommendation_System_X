from pyspark.sql.functions import coalesce, col, concat, lit, round

from local_env import get_env, get_int
from spark_common import create_spark


MYSQL_JDBC_URL = (
    f"jdbc:mysql://{get_env('MYSQL_HOST', '127.0.0.1')}:{get_int('MYSQL_PORT', 3306)}"
    f"/{get_env('MYSQL_DATABASE', 'ecommerce')}"
    "?useUnicode=true&characterEncoding=utf8"
    "&serverTimezone=Asia/Shanghai"
    "&rewriteBatchedStatements=true"
)


def main() -> None:
    spark = create_spark(
        "import_item_mysql_from_iceberg",
        extra_packages=["com.mysql:mysql-connector-j:8.4.0"],
    )

    item_df = (
        spark.table("iceberg.ods.ad_feature")
        .select(
            coalesce(col("adgroup_id"), lit(0)).alias("id"),
            concat(
                lit("广告商品 "),
                coalesce(col("adgroup_id").cast("string"), lit("0")),
                lit(" · 类目 "),
                coalesce(col("cate_id").cast("string"), lit("0")),
                lit(" · 品牌 "),
                coalesce(col("brand").cast("string"), lit("未知")),
            ).alias("title"),
            coalesce(col("cate_id"), lit(0)).alias("category_id"),
            coalesce(col("brand"), lit(0)).alias("brand_id"),
            coalesce(round(col("price"), 2), lit(0.0)).alias("price"),
            lit(None).cast("string").alias("image_url"),
            lit(1).cast("int").alias("status"),
        )
    )

    item_df.write.mode("append").format("jdbc").options(
        url=MYSQL_JDBC_URL,
        dbtable="item",
        user=get_env("MYSQL_USER"),
        password=get_env("MYSQL_PASSWORD"),
        driver="com.mysql.cj.jdbc.Driver",
        batchsize="10000",
    ).save()

    source_count = spark.table("iceberg.ods.ad_feature").count()
    print(f"Iceberg ad_feature rows: {source_count}")
    spark.stop()


if __name__ == "__main__":
    main()
