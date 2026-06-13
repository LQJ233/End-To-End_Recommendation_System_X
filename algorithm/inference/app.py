"""FastAPI entry point for the on-line inference service.

Run with:
    uvicorn algorithm.inference.app:app --host 0.0.0.0 --port 9000
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from algorithm.common.config_loader import get_config
from algorithm.inference.executors import shutdown as shutdown_pools
from algorithm.inference.model_registry import ModelRegistry
from algorithm.inference.service import InferenceService
from algorithm.inference.tracing import (
    TraceContextMiddleware, install_logging, request_id_ctx,
)

install_logging()
logger = logging.getLogger("inference")

app = FastAPI(title="End-To-End_Recommendation_System_X-inference", version="0.1.0")
app.add_middleware(TraceContextMiddleware)

# Prometheus: 鏆撮湶 /metrics, 鑷甫 http_* 鎸囨爣; 鑷畾涔夋寚鏍囧湪 metrics.py.
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
except Exception as e:
    logger.warning("prometheus instrumentator unavailable: %s", e)

_registry = ModelRegistry.from_config()
_service = InferenceService(_registry)


class RecallOptions(BaseModel):
    enableVectorRecall: bool = True
    enableLbsRecall: bool = True
    enableTagRecall: bool = True
    lbsMaxDistanceKm: Optional[float] = None
    tagDimensions: Optional[List[str]] = None


class RecommendRequest(BaseModel):
    requestId: str
    userId: str
    scene: str = "home"
    recallSize: int = Field(500, ge=1, le=2000)
    excludeItemIds: List[str] = Field(default_factory=list)
    recallOptions: RecallOptions = Field(default_factory=RecallOptions)


class ReloadRequest(BaseModel):
    modelVersion: str
    recallModelPath: Optional[str] = None
    rankingModelPath: Optional[str] = None
    featureConfigPath: Optional[str] = None


def _ok(data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    return {"code": 0, "message": "success", "requestId": request_id, "data": data}


def _err(code: int, message: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    return {"code": code, "message": message, "requestId": request_id, "data": None}


@app.get("/api/v1/inference/health")
def health():
    return _ok(_service.health())


@app.post("/api/v1/inference/recommend")
def recommend(req: RecommendRequest):
    # 鎶婃帹鑽?requestId 鍚屾鍒?logging context (瑕嗙洊 middleware 鐢?header 璁剧疆鐨勫崰浣?
    token = request_id_ctx.set(req.requestId)
    try:
        result = _service.recommend(req.model_dump())
        return _ok(result, request_id=req.requestId)
    except Exception as e:
        logger.exception("inference failure")
        return _err(500201, f"inference_error: {e}", request_id=req.requestId)
    finally:
        request_id_ctx.reset(token)


@app.post("/api/v1/inference/model/reload")
def reload_model(req: ReloadRequest):
    cfg = get_config().get("model", {})
    info = _registry.reload(
        req.modelVersion,
        req.recallModelPath or cfg.get("recallModelPath"),
        req.rankingModelPath or cfg.get("rankingModelPath"),
        req.featureConfigPath or cfg.get("featureConfigPath"),
    )
    return _ok(info)


@app.on_event("startup")
def warmup() -> None:
    try:
        _service.recommend({
            "requestId": "warmup",
            "userId": "__warmup__",
            "scene": "home",
            "recallSize": 8,
            "excludeItemIds": [],
            "recallOptions": {"enableVectorRecall": False, "enableLbsRecall": False, "enableTagRecall": False},
        })
        logger.info("warmup ok modelVersion=%s", _registry.model_version)
    except Exception as e:
        logger.warning("warmup failed: %s", e)


@app.on_event("shutdown")
def on_shutdown() -> None:
    shutdown_pools()
