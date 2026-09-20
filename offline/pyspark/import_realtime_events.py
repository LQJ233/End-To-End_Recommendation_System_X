from pyspark.sql.functions import col
from pyspark.sql.types import IntegerType, LongType, StringType, StructField, StructType

from spark_common import create_spark


REALTIME_PATH = "s3a://warehouse/realtime/behavior_events"

REALTIME_SCHEMA = StructType(
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


def normalize_realtime_events(dataframe):
    return dataframe.select(
        col("event_id").cast("string").alias("event_id"),
        col("user_id").cast("string").alias("user_id"),
        col("session_id").cast("string").alias("session_id"),
        col("item_id").cast("long").alias("item_id"),
        col("event_type").cast("string").alias("event_type"),
        col("page").cast("string").alias("page"),
        col("position").cast("int").alias("position"),
        col("source").cast("string").alias("source"),
        col("request_id").cast("string").alias("request_id"),
        col("recommendation_id").cast("string").alias("recommendation_id"),
        col("event_time").cast("long").alias("event_time"),
    )


def main() -> None:
    spark = create_spark("import_realtime_events_to_iceberg")
    spark.sql("CREATE DATABASE IF NOT EXISTS iceberg.ods")

    raw_events = spark.read.schema(REALTIME_SCHEMA).json(REALTIME_PATH)
    normalized = normalize_realtime_events(raw_events)
    normalized.writeTo("iceberg.ods.realtime_behavior_event").createOrReplace()

    print("realtime_behavior_event count:", spark.table(
        "iceberg.ods.realtime_behavior_event"
    ).count())
    spark.stop()


if __name__ == "__main__":
    main()
