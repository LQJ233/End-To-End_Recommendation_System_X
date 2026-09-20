import pytest
import asyncio

from app.artifacts import load_latest_bundle
from app.models import RecommendRequest
from app.pipeline.real_pipeline import RealPipeline


class FakeFeatureFetcher:
    def __init__(self, history=None, hot_items=None, user_features=None, cached_items=None):
        self.history = history or []
        self.hot_items = hot_items or []
        self.user_features = user_features or {}
        self.cached_items = cached_items or []

    async def get_user_history(self, user_id):
        return self.history

    async def get_hot_items(self, limit=20):
        return self.hot_items[:limit]

    async def get_user_features(self, user_id):
        return self.user_features

    async def get_cached_recall(self, user_id, limit=50):
        return self.cached_items[:limit]


def test_real_pipeline_executes_all_four_stages():
    bundle = load_latest_bundle()
    history_item = int(bundle.item_ids[0])
    hot_item = int(bundle.hot_items[0])
    pipeline = RealPipeline(
        FakeFeatureFetcher(history=[history_item], hot_items=[hot_item]),
        bundle,
    )

    candidates, trace = pytest.importorskip("asyncio").run(
        pipeline.run(RecommendRequest(user_id="real-user", size=5, debug=True))
    )

    assert len(candidates) == 5
    assert trace["recall_count"] >= trace["coarse_count"] >= trace["fine_count"] >= 5
    assert all(candidate.recall_source != "mock" for candidate in candidates)
    assert all(candidate.fine_score > 0 for candidate in candidates)


def test_real_pipeline_falls_back_to_popular_when_recall_times_out():
    bundle = load_latest_bundle()
    pipeline = RealPipeline(
        FakeFeatureFetcher(hot_items=bundle.hot_items[:10]),
        bundle,
    )

    class SlowRecall:
        async def recall(self, request):
            await asyncio.sleep(2)
            return []

    pipeline.recall = SlowRecall()
    candidates, trace = asyncio.run(
        pipeline.run(RecommendRequest(user_id="slow-user", size=5, debug=True))
    )

    assert len(candidates) == 5
    assert all(candidate.recall_source == "popular" for candidate in candidates)
    assert trace["recall_count"] >= 5


def test_real_pipeline_cold_start_uses_popular_items():
    bundle = load_latest_bundle()
    pipeline = RealPipeline(FakeFeatureFetcher(), bundle)

    candidates, _ = asyncio.run(
        pipeline.run(RecommendRequest(user_id="cold-start-user", size=5))
    )

    assert len(candidates) == 5
    assert all(candidate.recall_source == "popular" for candidate in candidates)


def test_real_pipeline_degrades_when_redis_is_unavailable():
    bundle = load_latest_bundle()

    class FailingFeatureFetcher:
        async def get_user_history(self, user_id):
            raise RuntimeError("redis unavailable")

        async def get_hot_items(self, limit=20):
            raise RuntimeError("redis unavailable")

        async def get_user_features(self, user_id):
            raise RuntimeError("redis unavailable")

    pipeline = RealPipeline(FailingFeatureFetcher(), bundle)
    candidates, trace = asyncio.run(
        pipeline.run(RecommendRequest(user_id="redis-down-user", size=5, debug=True))
    )

    assert len(candidates) == 5
    assert trace["recall_count"] >= 5
    assert all(candidate.recall_source == "popular" for candidate in candidates)


def test_real_pipeline_uses_cache_recall_candidates():
    bundle = load_latest_bundle()
    cached_item = int(bundle.item_ids[0])
    pipeline = RealPipeline(
        FakeFeatureFetcher(cached_items=[cached_item]),
        bundle,
    )

    candidates = asyncio.run(
        pipeline.recall.recall(RecommendRequest(user_id="cache-recall-user", size=5))
    )

    assert any(candidate.recall_source == "cache" for candidate in candidates)
