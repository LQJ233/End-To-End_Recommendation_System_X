import numpy as np


def roc_auc(labels, probabilities) -> float:
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities)
    positive_count = int((labels == 1).sum())
    negative_count = int((labels == 0).sum())
    if positive_count == 0 or negative_count == 0:
        return 0.5

    order = np.argsort(probabilities, kind="mergesort")
    sorted_scores = probabilities[order]
    ranks = np.empty(len(probabilities), dtype=float)
    index = 0
    while index < len(sorted_scores):
        end = index + 1
        while end < len(sorted_scores) and sorted_scores[end] == sorted_scores[index]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        ranks[order[index:end]] = average_rank
        index = end

    positive_rank_sum = ranks[labels == 1].sum()
    return float(
        (positive_rank_sum - positive_count * (positive_count + 1) / 2.0)
        / (positive_count * negative_count)
    )
