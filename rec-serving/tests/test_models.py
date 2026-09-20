import pytest
from pydantic import ValidationError

from app.models import Candidate, RecommendRequest


def test_recommend_request_defaults_are_stable():
    request = RecommendRequest()

    assert request.user_id == "anonymous"
    assert request.scene == "home"
    assert request.size == 20
    assert request.debug is False
    assert request.context == {}


@pytest.mark.parametrize("size", [0, 101])
def test_recommend_request_rejects_size_outside_range(size):
    with pytest.raises(ValidationError):
        RecommendRequest(size=size)


def test_candidate_defaults_are_zero_scores():
    candidate = Candidate(item_id=1001)

    assert candidate.recall_score == 0.0
    assert candidate.coarse_score == 0.0
    assert candidate.fine_score == 0.0
    assert candidate.rerank_score == 0.0
    assert candidate.recall_source == "mock"
