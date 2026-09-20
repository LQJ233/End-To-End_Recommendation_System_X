from build_cache_recall import build_cache_candidates


def test_build_cache_candidates_uses_preferred_categories(spark):
    clicks = spark.createDataFrame(
        [
            (1, 10, 1),
            (1, 20, 1),
            (2, 10, 1),
        ],
        ["user_id", "item_id", "label"],
    )
    item_features = spark.createDataFrame(
        [
            (10, 1),
            (20, 1),
            (30, 1),
            (40, 2),
        ],
        ["item_id", "category_id"],
    )
    item_scores = spark.createDataFrame(
        [
            (30, 100, 0.5),
            (40, 90, 0.4),
            (20, 10, 0.1),
        ],
        ["item_id", "click_cnt", "ctr"],
    )

    candidates = build_cache_candidates(
        clicks,
        item_features,
        item_scores,
        max_categories=1,
        limit=2,
        min_clicks=2,
    ).collect()

    assert len(candidates) == 1
    assert candidates[0].user_id == 1
    assert candidates[0].item_id == 30
