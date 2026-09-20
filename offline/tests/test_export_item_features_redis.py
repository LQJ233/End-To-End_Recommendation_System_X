from export_item_features_redis import write_item_features


class FakePipeline:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def hset(self, key, mapping):
        self.redis_client.hashes[key] = mapping

    def execute(self):
        return None


class FakeRedis:
    def __init__(self):
        self.hashes = {}

    def pipeline(self):
        return FakePipeline(self)


def test_write_item_features_uses_expected_redis_hash_keys():
    redis_client = FakeRedis()
    count = write_item_features(
        [
            {
                "item_id": 102,
                "category_id": 6406,
                "brand_id": 95471,
                "campaign_id": 1,
                "customer_id": 9,
                "price": 170.0,
            },
            {
                "item_id": 103,
                "category_id": 6407,
                "brand_id": 95472,
                "campaign_id": 2,
                "customer_id": 10,
                "price": 180.0,
            },
        ],
        redis_client,
        batch_size=1,
    )

    assert count == 2
    assert redis_client.hashes["adrec:item:features:102"]["category_id"] == 6406
    assert redis_client.hashes["adrec:item:features:102"]["brand_id"] == 95471
    assert redis_client.hashes["adrec:item:features:103"]["price"] == 180.0
