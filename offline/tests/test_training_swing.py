import pandas as pd

from training.swing import build_swing_similarity


def test_build_swing_similarity_ranks_co_clicked_items():
    clicks = pd.DataFrame(
        [
            {"user_id": 1, "item_id": 10},
            {"user_id": 1, "item_id": 20},
            {"user_id": 1, "item_id": 30},
            {"user_id": 2, "item_id": 10},
            {"user_id": 2, "item_id": 20},
            {"user_id": 3, "item_id": 20},
            {"user_id": 3, "item_id": 30},
        ]
    )

    similarity = build_swing_similarity(clicks, max_items_per_user=10, max_neighbors=2)

    assert set(similarity.columns) == {"item_id", "neighbor_item_id", "score"}
    top_for_10 = similarity[similarity["item_id"] == 10].iloc[0]
    assert top_for_10["neighbor_item_id"] == 20
    assert top_for_10["score"] > 0
    assert len(similarity[similarity["item_id"] == 10]) <= 2
