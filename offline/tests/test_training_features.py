import numpy as np
import pandas as pd

from training.features import build_vocab, encode_categoricals, normalize_price


def test_build_vocab_reserves_zero_for_unknown_values():
    vocab = build_vocab(pd.Series([10, 20, 20, 30]))

    assert vocab[10] == 1
    assert vocab[20] == 2
    assert vocab[30] == 3
    assert len(vocab) == 3


def test_encode_categoricals_maps_unknown_to_zero():
    dataframe = pd.DataFrame({"user_id": [10, 20, 999], "item_id": [100, 200, 100]})
    vocabs = {
        "user_id": build_vocab(pd.Series([10, 20])),
        "item_id": build_vocab(pd.Series([100, 200])),
    }

    encoded = encode_categoricals(dataframe, ["user_id", "item_id"], vocabs)

    assert encoded.shape == (3, 2)
    assert encoded.dtype == np.int64
    assert encoded[2, 0] == 0
    assert encoded[0, 0] == vocabs["user_id"][10]
    assert encoded[0, 1] == vocabs["item_id"][100]


def test_normalize_price_handles_zero_and_large_values():
    prices = pd.Series([0.0, 100.0, 10000.0])

    normalized = normalize_price(prices)

    assert normalized[0] == 0.0
    assert normalized[1] > 0.0
    assert normalized[2] > normalized[1]
    assert np.isfinite(normalized).all()
