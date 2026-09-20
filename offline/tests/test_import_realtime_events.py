from pyspark.sql.types import IntegerType, LongType, StringType, StructField, StructType

from import_realtime_events import normalize_realtime_events


def test_normalize_realtime_events_uses_expected_schema(spark):
    schema = StructType(
        [
            StructField("event_id", StringType(), True),
            StructField("user_id", StringType(), True),
            StructField("session_id", StringType(), True),
            StructField("item_id", LongType(), True),
            StructField("event_type", StringType(), True),
            StructField("page", StringType(), True),
            StructField("position", IntegerType(), True),
            StructField("source", StringType(), True),
            StructField("request_id", StringType(), True),
            StructField("recommendation_id", StringType(), True),
            StructField("event_time", LongType(), True),
        ]
    )
    dataframe = spark.createDataFrame(
        [
            (
                "evt-1",
                "user-1",
                "session-1",
                1001,
                "click",
                "home",
                1,
                "home_card",
                "req-1",
                "rec-1",
                1700000000000,
            )
        ],
        schema,
    )

    normalized = normalize_realtime_events(dataframe)
    row = normalized.collect()[0]

    assert row.event_id == "evt-1"
    assert row.item_id == 1001
    assert row.event_type == "click"
    assert row.event_time == 1700000000000
