import pytest

from app.features import FeatureFetcher


class FakeRedis:
    def __init__(self):
        self.lists = {
            "adrec:user:history:user-1": ["1001", "1002"],
            "adrec:hot:items": ["2001", "2002", "2003"],
            "adrec:recall:cache:user-1": ["3001", "3002"],
        }
        self.hashes = {
            "adrec:user:features:user-1": {"age_level": "3"},
            "adrec:item:features:1001": {"category_id": "6406"},
        }
        self.calls = []

    async def lrange(self, key, start, end):
        self.calls.append(("lrange", key, start, end))
        return self.lists.get(key, [])[start:end + 1]

    async def hgetall(self, key):
        self.calls.append(("hgetall", key))
        return self.hashes.get(key, {})


@pytest.mark.asyncio
async def test_get_user_history_parses_integer_item_ids():
    fetcher = FeatureFetcher(FakeRedis())

    assert await fetcher.get_user_history("user-1") == [1001, 1002]


@pytest.mark.asyncio
async def test_get_hot_items_respects_limit():
    redis = FakeRedis()
    fetcher = FeatureFetcher(redis)

    assert await fetcher.get_hot_items(limit=2) == [2001, 2002]
    assert redis.calls[-1] == ("lrange", "adrec:hot:items", 0, 1)


@pytest.mark.asyncio
async def test_get_feature_hashes_use_expected_keys():
    fetcher = FeatureFetcher(FakeRedis())

    assert await fetcher.get_user_features("user-1") == {"age_level": "3"}
    assert await fetcher.get_item_features(1001) == {"category_id": "6406"}


@pytest.mark.asyncio
async def test_get_cached_recall_reads_user_candidate_list():
    fetcher = FeatureFetcher(FakeRedis())

    assert await fetcher.get_cached_recall("user-1", limit=2) == [3001, 3002]
