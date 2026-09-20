from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_id: str = Field(default="anonymous")
    scene: str = Field(default="home")
    size: int = Field(default=20, ge=1, le=100)
    request_id: Optional[str] = None
    context: dict = Field(default_factory=dict)
    debug: bool = Field(default=False)


class Candidate(BaseModel):
    item_id: int
    recall_score: float = 0.0
    coarse_score: float = 0.0
    fine_score: float = 0.0
    rerank_score: float = 0.0
    recall_source: str = "mock"


class StageTrace(BaseModel):
    recall_count: int = 0
    coarse_count: int = 0
    fine_count: int = 0
    rerank_count: int = 0
    latency_ms: dict = Field(default_factory=dict)


class RecommendResponse(BaseModel):
    request_id: str
    user_id: str
    scene: str
    items: List[Candidate]
    trace: Optional[StageTrace] = None
