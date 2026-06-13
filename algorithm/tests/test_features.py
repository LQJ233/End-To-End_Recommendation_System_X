"""特征 transform 一致性测试: 同样的输入两次应该出同样的索引."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from algorithm.common.features.schema import FeatureConfig
from algorithm.common.features.id_mapping import hash_id
from algorithm.common.features.transform import (
    build_user_input, build_item_input, encode_categorical,
)


def test_hash_id_is_deterministic():
    assert hash_id("u_123", 1_000_000) == hash_id("u_123", 1_000_000)
    assert hash_id(None, 1_000_000) == 0
    assert hash_id("", 1_000_000) == 0
    assert hash_id("<UNK>", 1_000_000) == 0


def test_hash_id_within_vocab():
    for v in [10, 100, 100_000, 2_000_000]:
        idx = hash_id("anything_xyz", v)
        assert 0 <= idx < v


def test_build_user_input_uses_user_id_in_cat():
    fc = FeatureConfig()
    out = build_user_input("u_42", {"gender": 1, "age_level": "18_24"}, fc)
    assert out["cat"]["user_id"] == encode_categorical("user_id", "u_42", fc)
    assert len(out["cont"]) == len(fc.user_cont)
    assert len(out["click_seq"]) == fc.seq_max_len


def test_build_item_input_handles_missing_columns():
    fc = FeatureConfig()
    out = build_item_input({"item_id": "10001"}, fc)
    assert out["cat"]["item_id"] == encode_categorical("item_id", "10001", fc)
    for n in fc.item_cont:
        assert isinstance(out["cont"], list)
    assert all(isinstance(x, float) for x in out["cont"])
