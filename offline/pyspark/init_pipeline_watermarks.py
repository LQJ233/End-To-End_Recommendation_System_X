from pyspark.sql.functions import max as spark_max

from spark_common import create_spark
from watermark import set_watermark


def main() -> None:
    spark = create_spark("init_pipeline_watermarks")
    dwd_max = (
        spark.table("iceberg.dwd.behavior_event")
        .agg(spark_max("event_time"))
        .collect()[0][0]
    )
    value = int(dwd_max or 0)
    set_watermark("dwd.behavior_event", value)
    set_watermark("dws.behavior_event", value)
    set_watermark("ads.training_sample", value)
    print(f"initialized_watermark={value}")
    spark.stop()


if __name__ == "__main__":
    main()
