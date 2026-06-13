"""Apply the same feature transforms to training and inference inputs."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .schema import FeatureConfig
from .id_mapping import hash_id


def load_feature_config(path: str | Path) -> FeatureConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg = FeatureConfig()
    cfg.cont_mean = {k: float(v) for k, v in raw.get("cont_mean", {}).items()}
    cfg.cont_std = {k: float(v) for k, v in raw.get("cont_std", {}).items()}
    cfg.cat_vocab_size = {k: int(v) for k, v in raw.get("cat_vocab_size", {}).items()}
    cfg.unk_token = raw.get("unk_token", "<UNK>")
    cfg.embedding_dim = int(raw.get("embedding_dim", 16))
    cfg.seq_max_len = int(raw.get("seq_max_len", 20))
    return cfg


def save_feature_config(cfg: FeatureConfig, path: str | Path) -> None:
    out = {
        "cont_mean": cfg.cont_mean,
        "cont_std": cfg.cont_std,
        "cat_vocab_size": cfg.cat_vocab_size,
        "unk_token": cfg.unk_token,
        "embedding_dim": cfg.embedding_dim,
        "seq_max_len": cfg.seq_max_len,
    }
    Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize(name: str, value: float | None, cfg: FeatureConfig) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    mean = cfg.cont_mean.get(name, 0.0)
    std = cfg.cont_std.get(name, 1.0) or 1.0
    return (float(value) - mean) / std


def encode_categorical(name: str, raw: Any, cfg: FeatureConfig) -> int:
    vocab = cfg.cat_vocab_size.get(name, 100_000)
    return hash_id(raw, vocab)


def encode_sequence(name: str, seq: Sequence[Any] | None, cfg: FeatureConfig,
                    backing_cat_name: str = "item_id") -> List[int]:
    seq = list(seq or [])[-cfg.seq_max_len:]
    encoded = [encode_categorical(backing_cat_name, s, cfg) for s in seq]
    if len(encoded) < cfg.seq_max_len:
        encoded = [0] * (cfg.seq_max_len - len(encoded)) + encoded
    return encoded


def build_user_input(user_id: str, raw_features: Dict[str, Any], cfg: FeatureConfig) -> Dict[str, Any]:
    cat = {name: encode_categorical(name, raw_features.get(name, user_id if name == "user_id" else None), cfg)
           for name in cfg.user_cat}
    cat["user_id"] = encode_categorical("user_id", user_id, cfg)
    cont = [normalize(name, _to_float(raw_features.get(name)), cfg) for name in cfg.user_cont]
    click_seq = encode_sequence("click_seq", raw_features.get("click_seq"), cfg)
    cart_seq = encode_sequence("cart_seq", raw_features.get("cart_seq"), cfg)
    purchase_seq = encode_sequence("purchase_seq", raw_features.get("purchase_seq"), cfg)
    return {
        "cat": cat,
        "cont": cont,
        "click_seq": click_seq,
        "cart_seq": cart_seq,
        "purchase_seq": purchase_seq,
    }


def build_item_input(raw_item: Dict[str, Any], cfg: FeatureConfig) -> Dict[str, Any]:
    cat = {name: encode_categorical(name, raw_item.get(name), cfg) for name in cfg.item_cat}
    cont = [normalize(name, _to_float(raw_item.get(name)), cfg) for name in cfg.item_cont]
    return {"cat": cat, "cont": cont}


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
