from prepare_online_test_data import select_test_users


def test_select_test_users_filters_by_click_activity(spark):
    behavior = spark.createDataFrame(
        [
            (1, 1001, 1),
            (1, 1002, 1),
            (1, 1001, 1),
            (1, 1003, 0),
            (1, 1004, 0),
            (1, 1005, 0),
            (2, 1001, 1),
            (2, 1002, 0),
        ],
        ["user_id", "item_id", "label"],
    )

    selected = select_test_users(
        behavior,
        min_clicks=3,
        min_distinct_items=2,
        min_exposures=3,
        limit=10,
    ).collect()

    assert len(selected) == 1
    assert selected[0].user_id == 1
    assert selected[0].click_cnt == 3
    assert selected[0].expose_cnt == 3
    assert selected[0].distinct_item_cnt == 2
