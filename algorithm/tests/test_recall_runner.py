"""recall_runner.merge 加权聚合的单元测试; 不依赖 Redis."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# 把 config 加载替换成 in-memory dict, 避免读真实文件
FAKE_CONFIG = {
    "recommendation": {
        "recallMergeWeight": {"vector": 0.5, "tag": 0.2, "lbs": 0.15, "cache": 0.15},
        "vectorRecallSize": 100,
        "lbsRecallSize": 100,
        "tagRecallSize": 100,
        "tagRecallDimensions": ["item_category", "brand"],
        "lbsGeoHashPrefixLength": 5,
        "cacheRecallMaxSize": 50,
    },
    "redis": {"host": "localhost", "port": 6379, "database": 0},
}


@pytest.fixture(autouse=True)
def patch_config():
    with patch("algorithm.inference.recall_runner.get_config", return_value=FAKE_CONFIG):
        yield


def test_merge_weighted_sum():
    from algorithm.inference import recall_runner

    channels = {
        "vector": {"a": 1.0, "b": 0.5},
        "lbs":    {"b": 0.8},
        "tag":    {"a": 0.4, "c": 0.9},
    }
    merged = recall_runner.merge(channels)

    # a: 0.5*1.0 + 0.2*0.4 = 0.58
    # b: 0.5*0.5 + 0.15*0.8 = 0.37
    # c: 0.2*0.9 = 0.18
    assert merged["a"]["score"] == pytest.approx(0.58)
    assert merged["b"]["score"] == pytest.approx(0.37)
    assert merged["c"]["score"] == pytest.approx(0.18)
    assert set(merged["a"]["channels"]) == {"vector", "tag"}
    assert set(merged["b"]["channels"]) == {"vector", "lbs"}


def test_merge_empty_when_no_channels():
    from algorithm.inference import recall_runner
    assert recall_runner.merge({}) == {}


def test_tag_recall_skips_disallowed_dims():
    from algorithm.inference import recall_runner

    with patch.object(recall_runner.redis_client, "read_tag_index",
                      return_value=[("item1", 1.0)]):
        out = recall_runner.tag_recall(
            "u_1",
            tag_pref=[("item_category:300", 2.0),
                      ("style:street", 5.0),     # 不在 dims 白名单 -> 跳过
                      ("brand:nike", 1.0)],
        )
    # item1 出现在 item_category 和 brand 两路, score: 2.0*1.0 + 1.0*1.0 = 3.0, 归一化后 = 1.0
    assert "item1" in out
    assert out["item1"] == pytest.approx(1.0)


def test_tag_recall_returns_empty_without_tag_pref():
    from algorithm.inference import recall_runner
    assert recall_runner.tag_recall("u_1", tag_pref=[]) == {}


def test_lbs_recall_skips_when_no_geohash():
    from algorithm.inference import recall_runner
    assert recall_runner.lbs_recall("u_1", geohash=None) == {}


def test_lbs_recall_uses_prefix():
    from algorithm.inference import recall_runner

    captured = {}
    def fake_read_lbs(prefix, top_n):
        captured["prefix"] = prefix
        captured["top_n"] = top_n
        return [("itemA", 0.7)]

    with patch.object(recall_runner.redis_client, "read_lbs_index", side_effect=fake_read_lbs):
        out = recall_runner.lbs_recall("u_1", geohash="wx4g0a23")
    assert captured["prefix"] == "wx4g0"   # prefixLen=5
    assert out == {"itemA": 0.7}
