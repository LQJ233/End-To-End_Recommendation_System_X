from pyspark.sql.functions import col, lit, max as spark_max, when

from spark_common import create_spark
from watermark import get_watermark, set_watermark


PIPELINE_NAME = "dwd.behavior_event"


def to_dwd_behavior(realtime_behavior):
    """Normalize realtime ODS rows into the DWD behavior schema.

    ODS realtime events keep the tracking spec unit (epoch millis), while
    ``iceberg.dwd.behavior_event`` follows the offline Taobao dataset, which
    stores ``time_stamp`` as epoch seconds. The watermark comparison only
    makes sense once both sides share the same unit, so convert here.

    ``iceberg.dwd.behavior_event`` also declares ``user_id``/``item_id`` as
    BIGINT (dataset schema), so tracking ids are cast back to long. Events with
    non-numeric ids (only produced by smoke tests) are dropped instead of
    writing nulls into the warehouse.
    """
    return (
        realtime_behavior.select(
            col("user_id").cast("long").alias("user_id"),
            col("item_id").cast("long").alias("item_id"),
            (col("event_time") / 1000).cast("long").alias("event_time"),
            lit("realtime").alias("pid"),
            col("event_type"),
            when(col("event_type") == "click", lit(1)).otherwise(lit(0)).alias("label"),
        )
        .filter(col("user_id").isNotNull() & col("item_id").isNotNull())
    )


def select_new_behavior(behavior, watermark: int):
    return behavior.filter(col("event_time") > watermark)


def main() -> None:
    spark = create_spark("build_dwd_incremental")
    watermark = get_watermark(PIPELINE_NAME)

    realtime_behavior = spark.table("iceberg.ods.realtime_behavior_event")
    normalized_realtime = to_dwd_behavior(realtime_behavior)
    skipped_rows = realtime_behavior.count() - normalized_realtime.count()
    new_behavior = select_new_behavior(normalized_realtime, watermark)
    new_count = new_behavior.count()
    if new_count > 0:
        new_behavior.writeTo("iceberg.dwd.behavior_event").append()
        max_event_time = new_behavior.agg(spark_max("event_time")).collect()[0][0]
        set_watermark(PIPELINE_NAME, int(max_event_time))

    print(f"dwd_incremental_rows={new_count}")
    print(f"dwd_skipped_non_numeric_ids={skipped_rows}")
    print(f"dwd_watermark={get_watermark(PIPELINE_NAME)}")
    spark.stop()


if __name__ == "__main__":
    main()
