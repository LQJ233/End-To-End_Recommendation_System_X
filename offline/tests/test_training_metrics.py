from training.metrics import roc_auc


def test_roc_auc_handles_ties_and_ordering():
    score = roc_auc(
        labels=[0, 0, 1, 1],
        probabilities=[0.1, 0.4, 0.35, 0.8],
    )

    assert round(score, 4) == 0.75
