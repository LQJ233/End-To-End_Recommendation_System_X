from fastapi import APIRouter
from redis.asyncio import Redis
import time

from app.artifacts import ModelManager
from app.features import FeatureFetcher
from app.metrics import RECOMMEND_LATENCY, RECOMMEND_REQUESTS
from app.models import RecommendRequest, RecommendResponse, StageTrace
from app.pipeline.mock_pipeline import MockPipeline
from app.pipeline.real_pipeline import RealPipeline

router = APIRouter()
redis_client = Redis(host="127.0.0.1", port=6379, decode_responses=True)
feature_fetcher = FeatureFetcher(redis_client)

try:
    model_manager = ModelManager()
    pipeline = RealPipeline(feature_fetcher, model_manager.bundle)
except Exception:
    model_manager = None
    pipeline = MockPipeline(feature_fetcher)


@router.get("/v1/models")
async def current_model() -> dict:
    if model_manager is None:
        return {"version": None, "pipeline": type(pipeline).__name__}
    return {
        "version": model_manager.bundle.version,
        "pipeline": type(pipeline).__name__,
    }


@router.post("/v1/models/reload")
async def reload_model(version: str | None = None) -> dict:
    global pipeline
    if model_manager is None:
        raise RuntimeError("real model artifacts are not available")
    bundle = model_manager.reload(version)
    pipeline = RealPipeline(feature_fetcher, bundle)
    return {"version": bundle.version, "pipeline": type(pipeline).__name__}


@router.post("/v1/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest) -> RecommendResponse:
    started = time.perf_counter()
    try:
        candidates, trace = await pipeline.run(request)
        RECOMMEND_REQUESTS.labels(status="success").inc()
    except Exception:
        RECOMMEND_REQUESTS.labels(status="error").inc()
        raise
    finally:
        RECOMMEND_LATENCY.observe(time.perf_counter() - started)
    request_id = request.request_id or f"req-{id(request)}"

    return RecommendResponse(
        request_id=request_id,
        user_id=request.user_id,
        scene=request.scene,
        items=candidates,
        trace=StageTrace(
            recall_count=trace["recall_count"],
            coarse_count=trace["coarse_count"],
            fine_count=trace["fine_count"],
            rerank_count=trace["rerank_count"],
            latency_ms={
                "recall": trace["recall"],
                "coarse": trace["coarse"],
                "fine": trace["fine"],
                "rerank": trace["rerank"],
            },
        ) if request.debug else None,
    )
