from abc import ABC, abstractmethod
from typing import List

from app.models import Candidate, RecommendRequest


class Recall(ABC):
    @abstractmethod
    async def recall(self, request: RecommendRequest) -> List[Candidate]:
        raise NotImplementedError


class CoarseRanker(ABC):
    @abstractmethod
    async def rank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        raise NotImplementedError


class FineRanker(ABC):
    @abstractmethod
    async def rank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        raise NotImplementedError


class Reranker(ABC):
    @abstractmethod
    async def rerank(self, request: RecommendRequest, candidates: List[Candidate]) -> List[Candidate]:
        raise NotImplementedError
