"""Feature schema shared by training and inference.

Continuous and categorical specifications live here so the
``feature_config.json`` produced by training stays in lock-step with
the on-line transform.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

UNKNOWN_TOKEN = "<UNK>"

USER_CATEGORICAL: List[str] = [
    "user_id",
    "gender",
    "age_level",
]
USER_CONTINUOUS: List[str] = [
    "click_cnt_1h",
    "click_cnt_1d",
    "cart_cnt_1d",
    "purchase_cnt_7d",
]
USER_SEQUENCE: List[str] = [
    "click_seq",
    "cart_seq",
    "purchase_seq",
]

ITEM_CATEGORICAL: List[str] = [
    "item_id",
    "item_category",
    "brand",
    "price_bucket",
]
ITEM_CONTINUOUS: List[str] = [
    "exposure_cnt_7d",
    "click_cnt_7d",
    "cart_cnt_7d",
    "purchase_cnt_7d",
]

CROSS_CONTINUOUS: List[str] = [
    "user_item_category_pref",
    "user_brand_pref",
    "user_price_bucket_pref",
]


# 默认 vocab 大小. item_id 单独放大: 天池 ~620k items, 留 3x margin -> 2M;
# user_id 同理放大. 其余离散字段稀疏度低, 10 万足够.
DEFAULT_CAT_VOCAB_SIZE: Dict[str, int] = {
    "user_id": 1_000_000,
    "item_id": 2_000_000,
    "item_category": 100_000,
    "brand": 100_000,
    "price_bucket": 1_000,
    "gender": 8,
    "age_level": 32,
}


def default_cat_vocab() -> Dict[str, int]:
    return dict(DEFAULT_CAT_VOCAB_SIZE)


@dataclass
class FeatureConfig:
    user_cat: List[str] = field(default_factory=lambda: list(USER_CATEGORICAL))
    user_cont: List[str] = field(default_factory=lambda: list(USER_CONTINUOUS))
    item_cat: List[str] = field(default_factory=lambda: list(ITEM_CATEGORICAL))
    item_cont: List[str] = field(default_factory=lambda: list(ITEM_CONTINUOUS))
    cross_cont: List[str] = field(default_factory=lambda: list(CROSS_CONTINUOUS))
    cont_mean: Dict[str, float] = field(default_factory=dict)
    cont_std: Dict[str, float] = field(default_factory=dict)
    cat_vocab_size: Dict[str, int] = field(default_factory=default_cat_vocab)
    unk_token: str = UNKNOWN_TOKEN
    embedding_dim: int = 16
    seq_max_len: int = 20
