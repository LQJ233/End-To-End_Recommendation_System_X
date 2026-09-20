from build_ads import DEFAULT_BEHAVIOR_LIMIT, build_training_sample


def test_default_behavior_limit_is_one_million():
    assert DEFAULT_BEHAVIOR_LIMIT == 1_000_000


def test_build_training_sample_respects_limits_and_joins_features(spark):
    behavior = spark.createDataFrame(
        [
            (1, 1, 1001, "p1", "click", 1),
            (2, 1, 1002, "p1", "expose", 0),
            (3, 1, 1003, "p1", "click", 1),
            (4, 2, 1004, "p1", "expose", 0),
            (5, 2, 1005, "p1", "expose", 0),
        ],
        ["user_id", "item_id", "event_time", "pid", "event_type", "label"],
    )
    item = spark.createDataFrame(
        [
            (1001, 6406, 1, 9, 10, 170.0),
            (1002, 6407, 2, 9, 11, 180.0),
            (1003, 6408, 3, 9, 12, 190.0),
            (1004, 6409, 4, 9, 13, 200.0),
            (1005, 6410, 5, 9, 14, 210.0),
        ],
        ["item_id", "category_id", "campaign_id", "customer_id", "brand_id", "price"],
    )
    user = spark.createDataFrame(
        [(1, 1, 2, 1, 3, 2, 1, 0, 4), (2, 2, 3, 1, 4, 3, 2, 1, 5)],
        [
            "user_id",
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

    sample = build_training_sample(
        behavior,
        item,
        user,
        positive_limit=1,
        negative_limit=2,
    )
    rows = sample.collect()

    assert len(rows) == 3
    assert sum(row.label for row in rows) == 1
    assert {row.label for row in rows} == {0, 1}
    assert {"label", "user_id", "item_id", "category_id", "age_level"}.issubset(sample.columns)
