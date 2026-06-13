"""Run the four recall channels and merge candidates.

Each channel returns ``Dict[item_id, score]``. Merge sums weighted scores;
weights come from conf/application-local.yml ``recommendation.recallMergeWeight``.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from algorithm.common.config_loader import get_config
from algorithm.inference import redis_client


def vector_recall(item_scores: Iterable[Tuple[str, float]]) -> Dict[str, float]:
    return {iid: float(s) for iid, s in item_scores}


def lbs_recall(user_id: str, geohash: str | None = None) -> Dict[str, float]:
    """如果调用方已经把 geohash 预读好就直接传, 省掉一次 RTT."""
    cfg = get_config()
    if geohash is None:
        geohash = redis_client.read_user_geohash(user_id)
    if not geohash:
        return {}
    prefix_len = int(cfg["recommendation"].get("lbsGeoHashPrefixLength", 5))
    prefix = geohash[:prefix_len]
    top_n = int(cfg["recommendation"].get("lbsRecallSize", 200))
    return {iid: float(s) for iid, s in redis_client.read_lbs_index(prefix, top_n)}


def tag_recall(user_id: str,
               tag_pref: list[tuple[str, float]] | None = None) -> Dict[str, float]:
    """tag_pref 已经在 bundle 里拿过的话直接传, 节省一次 ZREVRANGE."""
    cfg = get_config()
    dims = set(cfg["recommendation"].get("tagRecallDimensions", []))
    if not dims:
        return {}
    if tag_pref is None:
        tag_pref = redis_client.read_user_tag_pref(user_id, top_n=10)
    out: Dict[str, float] = {}
    top_per_tag = max(20, int(cfg["recommendation"].get("tagRecallSize", 300)) // 5)
    for member, user_score in tag_pref:
        try:
            tag_type, tag_value = member.split(":", 1)
        except ValueError:
            continue
        if tag_type not in dims:
            continue
        for iid, item_w in redis_client.read_tag_index(tag_type, tag_value, top_per_tag):
            out[iid] = out.get(iid, 0.0) + user_score * item_w
    if not out:
        return out
    mx = max(out.values()) or 1.0
    return {k: v / mx for k, v in out.items()}


def cache_recall(user_id: str) -> Dict[str, float]:
    cfg = get_config()
    n = int(cfg["recommendation"].get("cacheRecallMaxSize", 50))
    return {iid: float(s) for iid, s in redis_client.read_cache_recall(user_id, n)}


def hot_recall(top_n: int) -> Dict[str, float]:
    out = {iid: float(s) for iid, s in redis_client.read_hot_items(top_n)}
    if not out:
        return out
    mx = max(out.values()) or 1.0
    return {k: v / mx for k, v in out.items()}


def merge(channels: Dict[str, Dict[str, float]]) -> Dict[str, dict]:
    cfg = get_config()
    weights = cfg["recommendation"].get("recallMergeWeight", {
        "vector": 0.5, "tag": 0.2, "lbs": 0.15, "cache": 0.15,
    })
    merged: Dict[str, dict] = {}
    for ch_name, items in channels.items():
        w = float(weights.get(ch_name, 0.0))
        for iid, score in items.items():
            row = merged.setdefault(iid, {"channels": [], "score": 0.0})
            row["channels"].append(ch_name)
            row["score"] += w * score
    return merged
