"""Holds loaded models for the lifetime of the inference process.

On startup we *try* to load the user tower and ranker from disk; if files
are missing we fall back to a freshly-initialised model so the service can
still respond (with random-ish ranking) during early dev.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import torch

from algorithm.common.config_loader import get_config
from algorithm.common.features.schema import FeatureConfig
from algorithm.common.features.transform import load_feature_config
from algorithm.ranking.mmoe import MMoERanking
from algorithm.recall.two_tower import TwoTowerModel


@dataclass
class ModelRegistry:
    model_version: str = "00000000_0000"
    feature_config: FeatureConfig = field(default_factory=FeatureConfig)
    recall_model: Optional[TwoTowerModel] = None
    ranking_model: Optional[MMoERanking] = None
    recall_loaded: bool = False
    ranking_loaded: bool = False

    @classmethod
    def from_config(cls) -> "ModelRegistry":
        cfg = get_config()
        m_cfg = cfg.get("model", {})
        reg = cls(model_version=m_cfg.get("modelVersion", "00000000_0000"))
        fc_path = m_cfg.get("featureConfigPath")
        if fc_path and Path(fc_path).exists():
            try:
                reg.feature_config = load_feature_config(fc_path)
            except Exception:
                pass
        reg._build_default_models()
        reg._load_state(m_cfg.get("recallModelPath"), m_cfg.get("rankingModelPath"))
        return reg

    def _build_default_models(self) -> None:
        fc = self.feature_config
        user_cat_vocabs = {n: fc.cat_vocab_size.get(n, 100_000) for n in fc.user_cat}
        item_cat_vocabs = {n: fc.cat_vocab_size.get(n, 100_000) for n in fc.item_cat}
        self.recall_model = TwoTowerModel(
            user_cat_vocabs, item_cat_vocabs,
            len(fc.user_cont), len(fc.item_cont),
            emb_dim=fc.embedding_dim,
        )
        self.ranking_model = MMoERanking(
            user_cat_vocabs, item_cat_vocabs,
            len(fc.user_cont), len(fc.item_cont), len(fc.cross_cont),
            emb_dim=fc.embedding_dim,
        )

    def _load_state(self, recall_path: str | None, ranking_path: str | None) -> None:
        if recall_path and Path(recall_path).exists() and self.recall_model is not None:
            try:
                self.recall_model.load_state_dict(torch.load(recall_path, map_location="cpu"))
                self.recall_loaded = True
            except Exception:
                self.recall_loaded = False
        if ranking_path and Path(ranking_path).exists() and self.ranking_model is not None:
            try:
                self.ranking_model.load_state_dict(torch.load(ranking_path, map_location="cpu"))
                self.ranking_loaded = True
            except Exception:
                self.ranking_loaded = False
        if self.recall_model is not None:
            self.recall_model.eval()
        if self.ranking_model is not None:
            self.ranking_model.eval()

    def reload(self, version: str, recall_path: str | None, ranking_path: str | None,
               feature_config_path: str | None) -> Dict[str, Any]:
        if feature_config_path and Path(feature_config_path).exists():
            self.feature_config = load_feature_config(feature_config_path)
            self._build_default_models()
        self._load_state(recall_path, ranking_path)
        self.model_version = version
        return {"loaded": True, "modelVersion": version,
                "recallLoaded": self.recall_loaded, "rankingLoaded": self.ranking_loaded}
