"""Thin wrapper around redis-py for the inference service."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import redis

from algorithm.common.config_loader import get_config


_pool = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        cfg = get_config()["redis"]
        _pool = redis.ConnectionPool(
            host=cfg["host"],
            port=int(cfg["port"]),
            db=int(cfg.get("database", 0)),
            password=cfg.get("password") or None,
            decode_responses=True,
        )
    return redis.Redis(connection_pool=_pool)


@dataclass
class UserBundle:
    """一次 pipeline 拿回的用户在线特征集合."""
    features: Dict[str, str] = field(default_factory=dict)
    click_seq: List[str] = field(default_factory=list)
    cart_seq: List[str] = field(default_factory=list)
    purchase_seq: List[str] = field(default_factory=list)
    last_geo: Optional[str] = None
    tag_pref: List[tuple[str, float]] = field(default_factory=list)


def read_user_bundle(user_id: str, seq_len: int = 20, tag_top_n: int = 10) -> UserBundle:
    """
    把 6 次 Redis 调用合成一次 pipeline (single round trip).
    包括: HGETALL + 3 LRANGE + GET + ZREVRANGE.
    """
    r = get_redis()
    pipe = r.pipeline(transaction=False)
    pipe.hgetall(f"feature:user:{user_id}")
    pipe.lrange(f"feature:user:click_seq:{user_id}", 0, seq_len - 1)
    pipe.lrange(f"feature:user:cart_seq:{user_id}", 0, seq_len - 1)
    pipe.lrange(f"feature:user:purchase_seq:{user_id}", 0, seq_len - 1)
    pipe.get(f"feature:user:last_geo:{user_id}")
    pipe.zrevrange(f"feature:user:tag_pref:{user_id}", 0, tag_top_n - 1, withscores=True)
    try:
        results = pipe.execute()
    except Exception:
        # Redis 异常时返回空 bundle, 让上层走默认值 / fallback
        return UserBundle()
    return UserBundle(
        features=results[0] or {},
        click_seq=results[1] or [],
        cart_seq=results[2] or [],
        purchase_seq=results[3] or [],
        last_geo=results[4],
        tag_pref=[(m, float(s)) for m, s in (results[5] or [])],
    )


# ---- 单独的小工具仍保留, 给标签/LBS/缓存/热门召回用 (这些 key 与 user_id 解耦) ----

def read_user_features(user_id: str) -> Dict[str, str]:
    r = get_redis()
    return r.hgetall(f"feature:user:{user_id}") or {}


def read_user_seq(user_id: str, kind: str, limit: int = 20) -> List[str]:
    r = get_redis()
    return r.lrange(f"feature:user:{kind}:{user_id}", 0, limit - 1) or []


def read_user_tag_pref(user_id: str, top_n: int = 10) -> List[tuple[str, float]]:
    r = get_redis()
    items = r.zrevrange(f"feature:user:tag_pref:{user_id}", 0, top_n - 1, withscores=True)
    return [(m, float(s)) for m, s in items]


def read_user_geohash(user_id: str) -> Optional[str]:
    r = get_redis()
    return r.get(f"feature:user:last_geo:{user_id}")


def read_tag_index(tag_type: str, tag_value: str, top_n: int = 200) -> List[tuple[str, float]]:
    r = get_redis()
    items = r.zrevrange(f"rec:tag:index:{tag_type}:{tag_value}", 0, top_n - 1, withscores=True)
    return [(m, float(s)) for m, s in items]


def read_lbs_index(geohash_prefix: str, top_n: int = 200) -> List[tuple[str, float]]:
    r = get_redis()
    items = r.zrevrange(f"rec:lbs:index:{geohash_prefix}", 0, top_n - 1, withscores=True)
    return [(m, float(s)) for m, s in items]


def read_cache_recall(user_id: str, top_n: int = 50) -> List[tuple[str, float]]:
    r = get_redis()
    items = r.zrevrange(f"rec:cache:{user_id}", 0, top_n - 1, withscores=True)
    return [(m, float(s)) for m, s in items]


def read_hot_items(top_n: int = 500) -> List[tuple[str, float]]:
    r = get_redis()
    items = r.zrevrange("rec:hot:items", 0, top_n - 1, withscores=True)
    return [(m, float(s)) for m, s in items]
