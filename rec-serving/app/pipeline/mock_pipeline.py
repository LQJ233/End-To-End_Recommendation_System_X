import random
import time
from typing import List

from app.features import FeatureFetcher
from app.models import Candidate, RecommendRequest
from app.pipeline.base import CoarseRanker, FineRanker, Recall, Reranker


MOCK_ITEM_IDS = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008]


class MockRecall(Recall):
    def __init__(self, feature_fetcher: FeatureFetcher) -> None:
        self.feature_fetcher = feature_fetcher

    async def recall(self, request: RecommendRequest) -> List[Candidate]:
        seed = sum(ord(char) for char in request.user_id)
        candidates = []
        seen_item_ids = set()

        def append_candidate(item_id: int, score: float, source: str) -> None:
            if item_id in seen_item_ids:
                return
            seen_item_ids.add(item_id)
            candidates.append(
                Candidate(
                    item_id=item_id,
                    recall_score=round(score, 4),
                    recall_source=source,
                )
            )

        try:
            user_history = await self.feature_fetcher.get_user_history(request.user_id)
            hot_items = await self.feature_fetcher.get_hot_items()
            priority_items = list(dict.fromkeys(user_history + hot_items))
            for item_id in priority_items:
                append_candidate(item_id, random.uniform(0.7, 1.0), "redis")
        except Exception:
            priority_items = []

        for index in range(24):
            item_id = MOCK_ITEM_IDS[(seed + index) % len(MOCK_ITEM_IDS)]
            append_candidate(item_id, random.uniform(0.5, 1.0), "mock")
        return candidates


class MockCoarseRanker(CoarseRanker):
    async def rank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        for candidate in candidates:
            candidate.coarse_score = round(random.uniform(0.4, 0.9), 4)
        ranked = sorted(candidates, key=lambda item: item.coarse_score, reverse=True)
        return ranked[:12]


class MockFineRanker(FineRanker):
    async def rank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        for candidate in candidates:
            candidate.fine_score = round(random.uniform(0.1, 0.8), 4)
        ranked = sorted(candidates, key=lambda item: item.fine_score, reverse=True)
        return ranked[:request.size]


class MockReranker(Reranker):
    async def rerank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        for candidate in candidates:
            candidate.rerank_score = round(candidate.fine_score + random.uniform(-0.05, 0.05), 4)
        return sorted(candidates, key=lambda item: item.rerank_score, reverse=True)


class MockPipeline:
    def __init__(self, feature_fetcher: FeatureFetcher) -> None:
        self.recall = MockRecall(feature_fetcher)
        self.coarse = MockCoarseRanker()
        self.fine = MockFineRanker()
        self.rerank = MockReranker()

    async def run(self, request: RecommendRequest):
        trace = {}

        start = time.perf_counter()
        candidates = await self.recall.recall(request)
        trace["recall_count"] = len(candidates)
        trace["recall"] = round((time.perf_counter() - start) * 1000, 2)

        start = time.perf_counter()
        candidates = await self.coarse.rank(request, candidates)
        trace["coarse_count"] = len(candidates)
        trace["coarse"] = round((time.perf_counter() - start) * 1000, 2)

        start = time.perf_counter()
        candidates = await self.fine.rank(request, candidates)
        trace["fine_count"] = len(candidates)
        trace["fine"] = round((time.perf_counter() - start) * 1000, 2)

        start = time.perf_counter()
        candidates = await self.rerank.rerank(request, candidates)
        trace["rerank_count"] = len(candidates)
        trace["rerank"] = round((time.perf_counter() - start) * 1000, 2)

        return candidates, trace
