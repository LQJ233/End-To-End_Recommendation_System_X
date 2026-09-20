from prometheus_client import Counter, Histogram


RECOMMEND_REQUESTS = Counter(
    "rec_serving_recommend_requests_total",
    "Total recommendation requests",
    ["status"],
)

RECOMMEND_LATENCY = Histogram(
    "rec_serving_recommend_latency_seconds",
    "Recommendation request latency in seconds",
)
