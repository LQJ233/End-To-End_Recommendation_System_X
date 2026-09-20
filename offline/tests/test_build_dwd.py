from build_dwd import build_behavior_event_df, build_item_df, build_user_df
from pyspark.sql.types import DoubleType, LongType, StructField, StructType


def test_build_behavior_event_df_maps_click_and_expose(spark):
    raw = spark.createDataFrame(
        [
            (1, 1700000000, 1001, "p1", 0, 1),
            (1, 1700000001, 1002, "p2", 1, 0),
        ],
        ["user", "time_stamp", "adgroup_id", "pid", "nonclk", "clk"],
    )

    result = build_behavior_event_df(raw).orderBy("item_id").collect()

    assert result[0].user_id == 1
    assert result[0].item_id == 1001
    assert result[0].event_type == "click"
    assert result[0].label == 1
    assert result[1].event_type == "expose"
    assert result[1].label == 0


def test_build_item_df_replaces_null_features(spark):
    ad_feature = spark.createDataFrame(
        [(1001, 6406, None, 1, None, 170.0)],
        StructType(
            [
                StructField("adgroup_id", LongType(), True),
                StructField("cate_id", LongType(), True),
                StructField("campaign_id", LongType(), True),
                StructField("customer", LongType(), True),
                StructField("brand", LongType(), True),
                StructField("price", DoubleType(), True),
            ]
        ),
    )

    row = build_item_df(ad_feature).collect()[0]

    assert row.item_id == 1001
    assert row.category_id == 6406
    assert row.campaign_id == 0
    assert row.customer_id == 1
    assert row.brand_id == 0
    assert row.price == 170.0


def test_build_user_df_renames_user_id(spark):
    user_profile = spark.createDataFrame(
        [(7, 1, 2, 1, 3, 2, 1, 0, 4)],
        [
            "userid",
            "cms_segid",
            "cms_group_id",
            "final_gender_code",
            "age_level",
            "pvalue_level",
            "shopping_level",
            "occupation",
            "new_user_class_level",
        ],
    )

    row = build_user_df(user_profile).collect()[0]

    assert row.user_id == 7
    assert row.age_level == 3
    assert row.new_user_class_level == 4
