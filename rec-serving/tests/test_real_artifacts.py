from app.artifacts import encode_categorical_value, load_latest_bundle


def test_latest_training_bundle_contains_required_online_artifacts():
    bundle = load_latest_bundle()

    assert bundle.version.startswith("v")
    assert len(bundle.item_ids) > 0
    assert bundle.item_embeddings.shape[0] == len(bundle.item_ids)
    assert bundle.onnx_session is not None
    assert bundle.hot_items
    assert bundle.swing_index
    assert bundle.item_features


def test_encode_categorical_value_maps_unknown_to_zero():
    vocab = {"102": 1, "9285": 2}

    assert encode_categorical_value(102, vocab) == 1
    assert encode_categorical_value("9285", vocab) == 2
    assert encode_categorical_value(999999, vocab) == 0
    assert encode_categorical_value(None, vocab) == 0
