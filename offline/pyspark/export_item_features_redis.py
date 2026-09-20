import redis

from spark_common import create_spark


def write_item_features(rows, redis_client, batch_size: int = 1000) -> int:
    count = 0
    pipeline = redis_client.pipeline()
    with pipeline:
        for row in rows:
            item_id = int(row["item_id"])
            pipeline.hset(
                f"adrec:item:features:{item_id}",
                mapping={
                    "category_id": int(row["category_id"]),
                    "brand_id": int(row["brand_id"]),
                    "campaign_id": int(row["campaign_id"]),
                    "customer_id": int(row["customer_id"]),
                    "price": float(row["price"]),
                },
            )
            count += 1
            if count % batch_size == 0:
                pipeline.execute()
        pipeline.execute()
    return count


def main() -> None:
    spark = create_spark("export_item_features_redis")
    redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    rows = (
        row.asDict()
        for row in spark.table("iceberg.dwd.item")
        .select("item_id", "category_id", "brand_id", "campaign_id", "customer_id", "price")
        .toLocalIterator()
    )
    count = write_item_features(rows, redis_client)
    print(f"item_features_written={count}")
    spark.stop()


if __name__ == "__main__":
    main()
