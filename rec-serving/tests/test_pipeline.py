import pytest

from app.models import Candidate, RecommendRequest
from app.pipeline.mock_pipeline import (
    MockCoarseRanker,
    MockFineRanker,
    MockPipeline,
    MockRecall,
    MockReranker,
)


class FakeFeatureFetcher:
    def __init__(self, history=None, hot_items=None, fail=False):
        self.history = history or []
        self.hot_items = hot_items or []
        self.fail = fail

    async def get_user_history(self, user_id):
        if self.fail:
            raise RuntimeError("redis unavailable")
        return self.history

    async def get_hot_items(self, limit=20):
        if self.fail:
            raise RuntimeError("redis unavailable")
        return self.hot_items


@pytest.mark.asyncio
async def test_mock_recall_prioritizes_redis_items_and_deduplicates_candidates():
    recall = MockRecall(FakeFeatureFetcher(history=[1001], hot_items=[1002]))

    candidates = await recall.recall(RecommendRequest(user_id="user-1"))
    item_ids = [candidate.item_id for candidate in candidates]

    assert item_ids[:2] == [1001, 1002]
    assert len(item_ids) == len(set(item_ids))
    assert candidates[0].recall_source == "redis"


@pytest.mark.asyncio
async def test_mock_recall_falls_back_to_mock_when_redis_fails():
    recall = MockRecall(FakeFeatureFetcher(fail=True))

    candidates = await recall.recall(RecommendRequest(user_id="user-1"))

    assert candidates
    assert all(candidate.recall_source == "mock" for candidate in candidates)


@pytest.mark.asyncio
async def test_rankers_respect_stage_limits():
    candidates = [Candidate(item_id=item_id) for item_id in range(1000, 1030)]
    request = RecommendRequest(size=5)

    coarse = await MockCoarseRanker().rank(request, candidates)
    fine = await MockFineRanker().rank(request, coarse)
    reranked = await MockReranker().rerank(request, fine)

    assert len(coarse) == 12
    assert len(fine) == 5
    assert len(reranked) == 5
    assert reranked == sorted(reranked, key=lambda item: item.rerank_score, reverse=True)


@pytest.mark.asyncio
async def test_pipeline_records_every_stage_in_trace():
    pipeline = MockPipeline(FakeFeatureFetcher(history=[1001], hot_items=[1002]))

    candidates, trace = await pipeline.run(RecommendRequest(user_id="user-1", size=3))

    assert len(candidates) == 3
    assert trace["recall_count"] >= trace["coarse_count"] >= trace["fine_count"] >= trace["rerank_count"]
    assert set(trace) == {
        "recall_count",
        "coarse_count",
        "fine_count",
        "rerank_count",
        "recall",
        "coarse",
        "fine",
        "rerank",
    }
