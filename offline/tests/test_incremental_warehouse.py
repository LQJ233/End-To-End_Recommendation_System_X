from build_ads_incremental import build_incremental_sample
from build_dwd_incremental import select_new_behavior, to_dwd_behavior
from build_dws_incremental import (
    build_incremental_item_stats,
    build_incremental_user_stats,
)


def behavior(spark):
    return spark.createDataFrame(
        [
            (1, 1001, 100, "p1", "click", 1),
            (1, 1002, 200, "p1", "expose", 0),
            (2, 1001, 300, "p1", "click", 1),
            (2, 1003, 400, "p1", "expose", 0),
        ],
        ["user_id", "item_id", "event_time", "pid", "event_type", "label"],
    )


def test_select_new_behavior_uses_watermark(spark):
    selected = select_new_behavior(behavior(spark), watermark=200).collect()

    assert [row.event_time for row in selected] == [300, 400]


def test_to_dwd_behavior_converts_millis_to_seconds(spark):
    realtime = spark.createDataFrame(
        [
            ("11", 1001, 1_500_000_000_000, "click"),
            ("12", 1002, 1_500_000_060_000, "expose"),
        ],
        ["user_id", "item_id", "event_time", "event_type"],
    )

    rows = to_dwd_behavior(realtime).orderBy("user_id").collect()

    assert rows[0].event_time == 1_500_000_000
    assert rows[1].event_time == 1_500_000_060
    assert rows[0].pid == "realtime"
    assert rows[0].label == 1
    assert rows[1].label == 0


def test_to_dwd_behavior_drops_non_numeric_ids(spark):
    realtime = spark.createDataFrame(
        [
            ("11", 1001, 1_500_000_000_000, "click"),
            ("verify-user-1", 1002, 1_500_000_060_000, "click"),
        ],
        ["user_id", "item_id", "event_time", "event_type"],
    )

    rows = to_dwd_behavior(realtime).collect()

    assert len(rows) == 1
    assert rows[0].user_id == 11


def test_select_new_behavior_after_normalization(spark):
    realtime = spark.createDataFrame(
        [
            ("11", 1001, 1_500_000_000_000, "click"),
            ("12", 1002, 1_500_000_120_000, "click"),
        ],
        ["user_id", "item_id", "event_time", "event_type"],
    )

    selected = select_new_behavior(to_dwd_behavior(realtime), watermark=1_500_000_060)

    assert [row.event_time for row in selected.collect()] == [1_500_000_120]


def test_build_incremental_item_stats(spark):
    rows = build_incremental_item_stats(behavior(spark)).orderBy("item_id").collect()

    item_1001 = rows[0]
    assert item_1001.item_id == 1001
    assert item_1001.expose_cnt == 2
    assert item_1001.click_cnt == 2
    assert item_1001.distinct_user_cnt == 2


def test_build_incremental_user_stats(spark):
    rows = build_incremental_user_stats(behavior(spark)).orderBy("user_id").collect()

    assert rows[0].user_id == 1
    assert rows[0].expose_cnt == 2
    assert rows[0].click_cnt == 1


def test_build_incremental_sample_joins_item_and_user(spark):
    item = spark.createDataFrame(
        [(1001, 6406, 1, 9, 10, 170.0), (1002, 6407, 2, 9, 11, 180.0),
         (1003, 6408, 3, 9, 12, 190.0)],
        ["item_id", "category_id", "campaign_id", "customer_id", "brand_id", "price"],
    )
    user = spark.createDataFrame(
        [(1, 1, 2, 1, 3, 2, 1, 0, 4), (2, 2, 3, 1, 4, 3, 2, 1, 5)],
        [
            "user_id", "cms_segid", "cms_group_id", "final_gender_code",
            "age_level", "pvalue_level", "shopping_level", "occupation",
            "new_user_class_level",
        ],
    )

    sample = build_incremental_sample(behavior(spark), item, user)

    assert sample.count() == 4
    assert {"label", "user_id", "item_id", "category_id", "age_level"}.issubset(
        sample.columns
    )
