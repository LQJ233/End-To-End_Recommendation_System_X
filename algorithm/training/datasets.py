"""PyTorch Datasets backed by the parquet files produced by Spark.

Time Split 强制:
    07_开发规范.md §5.4 要求 feature_time < label_time. 这里在 Dataset 加载阶段
    对 parquet 做硬过滤; 通过 ``enforce_time_split=True`` 控制 (默认开启).

    Spark 端会把 feature_time 写为 timestamp - 1, 应该天然满足;
    如果 parquet 文件来自其他来源, 这一层是最后的防穿越栅栏.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import torch
from torch.utils.data import Dataset

from algorithm.common.config_loader import get_config
from algorithm.common.features.schema import FeatureConfig
from algorithm.common.features.transform import (
    build_item_input, build_user_input,
)

logger = logging.getLogger("training.datasets")


def _load_parquet_dir(path: Path) -> pd.DataFrame:
    files = sorted(path.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"no parquet under {path}")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _enforce_time_split(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """丢掉 feature_time >= timestamp 的行 (穿越样本), 并打印计数."""
    try:
        cfg = get_config().get("training", {})
        enabled = bool(cfg.get("enforceTimeSplit", True))
    except Exception:
        enabled = True
    if not enabled:
        return df
    if "feature_time" not in df.columns or "timestamp" not in df.columns:
        logger.warning("[%s] missing feature_time/timestamp columns, skip time split", dataset_name)
        return df
    mask = df["feature_time"] < df["timestamp"]
    dropped = int((~mask).sum())
    if dropped:
        logger.warning("[%s] dropped %d/%d rows that violate feature_time < label_time",
                       dataset_name, dropped, len(df))
    return df[mask].reset_index(drop=True)


class RecallDataset(Dataset):
    def __init__(self, parquet_dir: str | Path, feature_config: FeatureConfig):
        df = _load_parquet_dir(Path(parquet_dir))
        self.df = _enforce_time_split(df, "recall")
        self.fc = feature_config

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict:
        row = self.df.iloc[idx]
        user_id = str(row["user_id"])
        item_id = str(row["item_id"])
        u = build_user_input(user_id, {}, self.fc)
        i = build_item_input({"item_id": item_id}, self.fc)
        return {
            "user_cat": u["cat"],
            "user_cont": u["cont"],
            "click_seq": u["click_seq"],
            "cart_seq": u["cart_seq"],
            "purchase_seq": u["purchase_seq"],
            "item_cat": i["cat"],
            "item_cont": i["cont"],
            "label": int(row.get("label", 1)),
        }


class RankingDataset(Dataset):
    def __init__(self, parquet_dir: str | Path, feature_config: FeatureConfig):
        df = _load_parquet_dir(Path(parquet_dir))
        self.df = _enforce_time_split(df, "ranking")
        self.fc = feature_config

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict:
        row = self.df.iloc[idx]
        user_id = str(row["user_id"])
        item_id = str(row["item_id"])
        u = build_user_input(user_id, {}, self.fc)
        i = build_item_input({"item_id": item_id}, self.fc)
        return {
            "user_cat": u["cat"],
            "user_cont": u["cont"],
            "item_cat": i["cat"],
            "item_cont": i["cont"],
            "cross_cont": [0.0 for _ in self.fc.cross_cont],
            "ctr_label": int(row.get("ctr_label", 0)),
            "cvr_label": int(row.get("cvr_label", 0)),
        }


def collate_recall(batch: List[Dict]) -> Dict:
    keys_cat_user = list(batch[0]["user_cat"].keys())
    keys_cat_item = list(batch[0]["item_cat"].keys())
    return {
        "user_in": {
            "cat": {k: torch.tensor([b["user_cat"][k] for b in batch], dtype=torch.long) for k in keys_cat_user},
            "cont": torch.tensor([b["user_cont"] for b in batch], dtype=torch.float32),
            "seqs": {
                "click_seq": torch.tensor([b["click_seq"] for b in batch], dtype=torch.long),
                "cart_seq": torch.tensor([b["cart_seq"] for b in batch], dtype=torch.long),
                "purchase_seq": torch.tensor([b["purchase_seq"] for b in batch], dtype=torch.long),
            },
        },
        "item_in": {
            "cat": {k: torch.tensor([b["item_cat"][k] for b in batch], dtype=torch.long) for k in keys_cat_item},
            "cont": torch.tensor([b["item_cont"] for b in batch], dtype=torch.float32),
        },
        "label": torch.tensor([b["label"] for b in batch], dtype=torch.float32),
    }


def collate_ranking(batch: List[Dict]) -> Dict:
    keys_cat_user = list(batch[0]["user_cat"].keys())
    keys_cat_item = list(batch[0]["item_cat"].keys())
    return {
        "user_in": {
            "cat": {k: torch.tensor([b["user_cat"][k] for b in batch], dtype=torch.long) for k in keys_cat_user},
            "cont": torch.tensor([b["user_cont"] for b in batch], dtype=torch.float32),
        },
        "item_in": {
            "cat": {k: torch.tensor([b["item_cat"][k] for b in batch], dtype=torch.long) for k in keys_cat_item},
            "cont": torch.tensor([b["item_cont"] for b in batch], dtype=torch.float32),
        },
        "cross_cont": torch.tensor([b["cross_cont"] for b in batch], dtype=torch.float32),
        "ctr_label": torch.tensor([b["ctr_label"] for b in batch], dtype=torch.long),
        "cvr_label": torch.tensor([b["cvr_label"] for b in batch], dtype=torch.long),
    }
