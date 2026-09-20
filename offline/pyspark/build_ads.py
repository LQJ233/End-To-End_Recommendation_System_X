from pyspark.sql.functions import broadcast, col

from spark_common import create_spark


DEFAULT_BEHAVIOR_LIMIT = 1_000_000
POSITIVE_LIMIT = 200_000
NEGATIVE_LIMIT = 800_000


def build_training_sample(behavior, item, user, positive_limit=POSITIVE_LIMIT, negative_limit=NEGATIVE_LIMIT):
    positive = behavior.filter(col("label") == 1).limit(positive_limit)
    negative = behavior.filter(col("label") == 0).limit(negative_limit)
    sampled = positive.unionByName(negative)

    return (
        sampled.alias("b")
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
    spark = create_spark("build_ads_training_sample")

    behavior = spark.table("iceberg.dwd.behavior_event")
    item = spark.table("iceberg.dwd.item")
    user = spark.table("iceberg.dwd.user")

    training_sample = build_training_sample(
        behavior,
        item,
        user,
        positive_limit=POSITIVE_LIMIT,
        negative_limit=NEGATIVE_LIMIT,
    )

    training_sample.writeTo("iceberg.ads.training_sample").createOrReplace()

    print("training_sample count:", spark.table("iceberg.ads.training_sample").count())
    spark.table("iceberg.ads.training_sample").select("label").groupBy("label").count().show()

    spark.stop()


if __name__ == "__main__":
    main()
