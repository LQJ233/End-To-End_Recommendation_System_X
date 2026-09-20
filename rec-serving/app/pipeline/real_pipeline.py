import asyncio
import math
import time
from typing import List

import numpy as np

from app.artifacts import ModelBundle
from app.features import FeatureFetcher
from app.models import Candidate, RecommendRequest
from app.pipeline.base import CoarseRanker, FineRanker, Recall, Reranker


def _price_bucket(price: float) -> int:
    if price <= 0:
        return 0
    return int(math.log10(price + 1.0) * 2)


class RealRecall(Recall):
    def __init__(self, feature_fetcher: FeatureFetcher, bundle: ModelBundle) -> None:
        self.feature_fetcher = feature_fetcher
        self.bundle = bundle

    async def recall(self, request: RecommendRequest) -> List[Candidate]:
        history: list[int] = []
        hot_items: list[int] = []
        try:
            history = await self.feature_fetcher.get_user_history(request.user_id)
            hot_items = await self.feature_fetcher.get_hot_items(limit=100)
        except Exception:
            history = []
            hot_items = []
        hot_items = hot_items or self.bundle.hot_items[:100]
        cached_items: list[int] = []
        try:
            cached_items = await self.feature_fetcher.get_cached_recall(
                request.user_id,
                limit=50,
            )
        except Exception:
            cached_items = []

        candidates: dict[int, Candidate] = {}

        def add(item_id: int, score: float, source: str) -> None:
            item_id = int(item_id)
            existing = candidates.get(item_id)
            if existing is None or score > existing.recall_score:
                candidates[item_id] = Candidate(
                    item_id=item_id,
                    recall_score=round(float(score), 6),
                    recall_source=source,
                )

        for cached_item in cached_items:
            add(cached_item, 0.6, "cache")

        for history_item in reversed(history[-20:]):
            for neighbor, score in self.bundle.swing_index.get(int(history_item), [])[:30]:
                add(neighbor, score, "swing")

        history_vectors = [
            vector
            for vector in (
                self.bundle.vector_for_item(item_id)
                for item_id in history[-20:]
            )
            if vector is not None
        ]
        if history_vectors:
            query_vector = np.mean(np.stack(history_vectors), axis=0)
            for hit in await asyncio.to_thread(self.bundle.search_milvus, query_vector, 200):
                add(hit["item_id"], hit["score"], "milvus")

        for item_id in hot_items:
            add(item_id, 0.01, "popular")
        if not candidates:
            for item_id in self.bundle.hot_items[:100]:
                add(item_id, 0.01, "popular")

        return sorted(
            candidates.values(),
            key=lambda candidate: candidate.recall_score,
            reverse=True,
        )[:200]


class TwoTowerCoarseRanker(CoarseRanker):
    def __init__(self, bundle: ModelBundle, history: list[int] | None = None) -> None:
        self.bundle = bundle
        self.history = history or []

    def set_history(self, history: list[int]) -> None:
        self.history = history

    async def rank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        return await asyncio.to_thread(self._rank_sync, candidates)

    def _rank_sync(self, candidates: List[Candidate]) -> List[Candidate]:
        history_vectors = [
            vector
            for vector in (
                self.bundle.vector_for_item(item_id)
                for item_id in self.history[-20:]
            )
            if vector is not None
        ]
        user_vector = (
            np.mean(np.stack(history_vectors), axis=0)
            if history_vectors
            else None
        )
        for candidate in candidates:
            item_vector = self.bundle.vector_for_item(candidate.item_id)
            if user_vector is None or item_vector is None:
                candidate.coarse_score = candidate.recall_score
            else:
                candidate.coarse_score = round(float(np.dot(user_vector, item_vector)), 6)
        return sorted(candidates, key=lambda item: item.coarse_score, reverse=True)[:100]


class DeepFMFineRanker(FineRanker):
    def __init__(self, feature_fetcher: FeatureFetcher, bundle: ModelBundle) -> None:
        self.feature_fetcher = feature_fetcher
        self.bundle = bundle

    async def rank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        try:
            user_features = await self.feature_fetcher.get_user_features(request.user_id)
        except Exception:
            user_features = {}
        return await asyncio.to_thread(
            self._rank_sync,
            request,
            candidates,
            user_features,
        )

    def _rank_sync(
        self,
        request: RecommendRequest,
        candidates: List[Candidate],
        user_features: dict,
    ) -> List[Candidate]:
        if not candidates:
            return candidates

        categorical = np.concatenate(
            [
                self.bundle.encode_features(
                    request.user_id,
                    user_features,
                    candidate.item_id,
                )
                for candidate in candidates
            ],
            axis=0,
        )
        numeric = np.asarray(
            [[math.log1p(max(self.bundle.price(candidate.item_id), 0.0))] for candidate in candidates],
            dtype=np.float32,
        )
        logits = self.bundle.onnx_session.run(
            None,
            {"categorical": categorical, "numeric": numeric},
        )[0]
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        for candidate, probability in zip(candidates, probabilities):
            candidate.fine_score = round(float(probability), 6)
        return sorted(candidates, key=lambda item: item.fine_score, reverse=True)[: request.size]


class MMRReranker(Reranker):
    def __init__(self, bundle: ModelBundle) -> None:
        self.bundle = bundle

    async def rerank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        return await asyncio.to_thread(self._rerank_sync, request, candidates)

    def _rerank_sync(
        self,
        request: RecommendRequest,
        candidates: List[Candidate],
    ) -> List[Candidate]:
        remaining = list(candidates)
        selected: list[Candidate] = []
        category_counts: dict[int, int] = {}
        brand_counts: dict[int, int] = {}
        price_bucket_counts: dict[int, int] = {}

        while remaining and len(selected) < request.size:
            best_candidate = None
            best_score = float("-inf")
            for candidate in remaining:
                features = self.bundle.item_features.get(candidate.item_id, {})
                category = int(features.get("category_id", 0) or 0)
                brand = int(features.get("brand_id", 0) or 0)
                bucket = _price_bucket(self.bundle.price(candidate.item_id))
                penalty = (
                    0.15 * category_counts.get(category, 0)
                    + 0.20 * brand_counts.get(brand, 0)
                    + 0.08 * price_bucket_counts.get(bucket, 0)
                )
                adjusted = candidate.fine_score - penalty
                if adjusted > best_score:
                    best_score = adjusted
                    best_candidate = candidate

            remaining.remove(best_candidate)
            features = self.bundle.item_features.get(best_candidate.item_id, {})
            category = int(features.get("category_id", 0) or 0)
            brand = int(features.get("brand_id", 0) or 0)
            bucket = _price_bucket(self.bundle.price(best_candidate.item_id))
            category_counts[category] = category_counts.get(category, 0) + 1
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
            price_bucket_counts[bucket] = price_bucket_counts.get(bucket, 0) + 1
            best_candidate.rerank_score = round(float(best_score), 6)
            selected.append(best_candidate)
        return selected


class RealPipeline:
    def __init__(
        self,
        feature_fetcher: FeatureFetcher,
        bundle: ModelBundle,
        recall_timeout_seconds: float = 1.0,
        coarse_timeout_seconds: float = 0.5,
        fine_timeout_seconds: float = 0.5,
        rerank_timeout_seconds: float = 0.2,
    ) -> None:
        self.feature_fetcher = feature_fetcher
        self.bundle = bundle
        self.recall_timeout_seconds = recall_timeout_seconds
        self.coarse_timeout_seconds = coarse_timeout_seconds
        self.fine_timeout_seconds = fine_timeout_seconds
        self.rerank_timeout_seconds = rerank_timeout_seconds
        self.recall = RealRecall(feature_fetcher, bundle)
        self.coarse = TwoTowerCoarseRanker(bundle)
        self.fine = DeepFMFineRanker(feature_fetcher, bundle)
        self.rerank = MMRReranker(bundle)

    def _popular_candidates(self, limit: int = 200) -> list[Candidate]:
        return [
            Candidate(
                item_id=int(item_id),
                recall_score=0.01,
                recall_source="popular",
            )
            for item_id in self.bundle.hot_items[:limit]
        ]

    @staticmethod
    async def _with_timeout(coro, timeout_seconds: float):
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except Exception:
            return None

    async def run(self, request: RecommendRequest):
        trace = {}

        start = time.perf_counter()
        try:
            history = await self.feature_fetcher.get_user_history(request.user_id)
        except Exception:
            history = []
        self.coarse.set_history(history)
        candidates = await self._with_timeout(
            self.recall.recall(request),
            self.recall_timeout_seconds,
        )
        if not candidates:
            candidates = self._popular_candidates()
        trace["recall_count"] = len(candidates)
        trace["recall"] = round((time.perf_counter() - start) * 1000, 2)

        start = time.perf_counter()
        coarse_candidates = await self._with_timeout(
            self.coarse.rank(request, candidates),
            self.coarse_timeout_seconds,
        )
        if coarse_candidates:
            candidates = coarse_candidates
        trace["coarse_count"] = len(candidates)
        trace["coarse"] = round((time.perf_counter() - start) * 1000, 2)

        start = time.perf_counter()
        fine_candidates = await self._with_timeout(
            self.fine.rank(request, candidates),
            self.fine_timeout_seconds,
        )
        if fine_candidates:
            candidates = fine_candidates
        trace["fine_count"] = len(candidates)
        trace["fine"] = round((time.perf_counter() - start) * 1000, 2)

        start = time.perf_counter()
        reranked_candidates = await self._with_timeout(
            self.rerank.rerank(request, candidates),
            self.rerank_timeout_seconds,
        )
        if reranked_candidates:
            candidates = reranked_candidates
        trace["rerank_count"] = len(candidates)
        trace["rerank"] = round((time.perf_counter() - start) * 1000, 2)
        return candidates, trace
