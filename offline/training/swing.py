from collections import Counter
from itertools import combinations
from math import sqrt

import pandas as pd


def build_swing_similarity(
    clicks: pd.DataFrame,
    max_items_per_user: int = 10,
    max_neighbors: int = 50,
) -> pd.DataFrame:
    interactions = (
        clicks[["user_id", "item_id"]]
        .dropna()
        .drop_duplicates()
        .groupby("user_id", sort=False)
        .head(max_items_per_user)
    )

    item_counts = Counter()
    pair_counts = Counter()
    for _, items in interactions.groupby("user_id", sort=False)["item_id"]:
        unique_items = sorted({int(item_id) for item_id in items.tolist()})
        item_counts.update(unique_items)
        for left, right in combinations(unique_items, 2):
            pair_counts[(left, right)] += 1

    rows = []
    for (left, right), count in pair_counts.items():
        score = count / sqrt(item_counts[left] * item_counts[right])
        rows.append((left, right, score))
        rows.append((right, left, score))

    if not rows:
        return pd.DataFrame(columns=["item_id", "neighbor_item_id", "score"])

    similarity = pd.DataFrame(
        rows,
        columns=["item_id", "neighbor_item_id", "score"],
    )
    similarity = similarity.sort_values(
        ["item_id", "score", "neighbor_item_id"],
        ascending=[True, False, True],
    )
    return similarity.groupby("item_id", sort=False).head(max_neighbors).reset_index(drop=True)
