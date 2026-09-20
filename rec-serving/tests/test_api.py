from fastapi.testclient import TestClient

from app.api import recommend as recommend_api
from app.main import app
from app.pipeline.mock_pipeline import MockPipeline


class FakeFeatureFetcher:
    async def get_user_history(self, user_id):
        return [1001]

    async def get_hot_items(self, limit=20):
        return [1002, 1003]


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint_exposes_recommend_metrics():
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "rec_serving_recommend_requests_total" in response.text
    assert "rec_serving_recommend_latency_seconds" in response.text


def test_recommend_endpoint_returns_requested_number_of_items(monkeypatch):
    monkeypatch.setattr(
        recommend_api,
        "pipeline",
        MockPipeline(FakeFeatureFetcher()),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/recommend",
        json={
            "user_id": "user-1",
            "scene": "home",
            "size": 4,
            "request_id": "req-test",
            "debug": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == "req-test"
    assert payload["user_id"] == "user-1"
    assert len(payload["items"]) == 4
    assert payload["trace"]["recall_count"] > 0
    assert payload["trace"]["rerank_count"] == 4


def test_recommend_without_debug_omits_trace(monkeypatch):
    monkeypatch.setattr(
        recommend_api,
        "pipeline",
        MockPipeline(FakeFeatureFetcher()),
    )
    client = TestClient(app)

    response = client.post("/v1/recommend", json={"user_id": "user-1", "size": 2})

    assert response.status_code == 200
    assert response.json()["trace"] is None


def test_model_status_reports_real_pipeline():
    client = TestClient(app)

    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"].startswith("v")
    assert payload["pipeline"] == "RealPipeline"


def test_real_recommend_endpoint_returns_model_candidates():
    client = TestClient(app)

    response = client.post(
        "/v1/recommend",
        json={"user_id": "real-smoke-user", "scene": "home", "size": 5, "debug": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 5
    assert all(item["recall_source"] != "mock" for item in payload["items"])
    assert payload["trace"]["coarse_count"] >= payload["trace"]["fine_count"] >= 5
