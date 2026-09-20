from pathlib import Path

import numpy as np

from training.train import (
    ALL_COLUMNS,
    ITEM_COLUMNS,
    USER_COLUMNS,
    train_deepfm,
    train_two_tower,
)


def test_training_loops_write_model_artifacts(tmp_path: Path):
    rng = np.random.default_rng(7)
    row_count = 256
    categorical = np.column_stack(
        [
            rng.integers(1, 20, size=row_count)
            for _ in ALL_COLUMNS
        ]
    ).astype(np.int64)
    numeric = rng.random((row_count, 1), dtype=np.float32)
    labels = (rng.random(row_count) > 0.5).astype(np.float32)
    vocabs = {
        column: {value: value for value in range(1, 20)}
        for column in ALL_COLUMNS
    }

    deepfm_metrics = train_deepfm(
        categorical,
        numeric,
        labels,
        vocabs,
        tmp_path,
        epochs=1,
        batch_size=64,
    )
    two_tower_metrics = train_two_tower(
        categorical,
        labels,
        vocabs,
        tmp_path,
        epochs=1,
        batch_size=64,
    )

    assert "auc" in deepfm_metrics
    assert "auc" in two_tower_metrics
    assert (tmp_path / "deepfm.pt").exists()
    assert (tmp_path / "two_tower.pt").exists()
    assert len(USER_COLUMNS) + len(ITEM_COLUMNS) == len(ALL_COLUMNS)
