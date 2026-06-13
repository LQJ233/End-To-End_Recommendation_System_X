"""自定义 Prometheus 指标 (推理服务).

prometheus-fastapi-instrumentator 会自动给我们出:
    - http_requests_total
    - http_request_duration_seconds (histogram)
    - http_request_size_bytes / response_size_bytes

这里加业务自定义:
    - recsys_recall_channel_size       : 每路召回返回的数量
    - recsys_recall_channel_latency_ms : 每路召回耗时
    - recsys_rank_latency_ms           : 排序耗时
    - recsys_fallback_total            : 各种 fallback 计数
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram

CHANNEL_SIZE = Histogram(
    "recsys_recall_channel_size",
    "Number of items returned by each recall channel",
    labelnames=("channel",),
    buckets=(0, 1, 5, 20, 50, 100, 200, 500, 1000),
)

CHANNEL_LATENCY_MS = Histogram(
    "recsys_recall_channel_latency_ms",
    "Per-channel recall latency in ms",
    labelnames=("channel",),
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500),
)

RANK_LATENCY_MS = Histogram(
    "recsys_rank_latency_ms",
    "Ranking latency in ms",
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000),
)

FALLBACK_TOTAL = Counter(
    "recsys_fallback_total",
    "Number of fallback triggers",
    labelnames=("reason",),    # recall_empty / ranking_timeout / ranking_failed / hot
)
