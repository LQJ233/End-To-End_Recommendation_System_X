import json
import os
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import pandas as pd
from pymilvus import MilvusClient


DEFAULT_MODEL_ROOT = Path(
    "/Users/qj/Item/End-To-End_Recommendation_System_X/offline/training_output"
)


def encode_categorical_value(value: Any, vocab: dict[str, int]) -> int:
    if value is None:
        return 0
    try:
        return vocab.get(str(int(value)), 0)
    except (TypeError, ValueError):
        return 0


@dataclass
class ModelBundle:
    version: str
    path: Path
    manifest: dict[str, Any]
    schema: dict[str, Any]
    item_ids: np.ndarray
    item_embeddings: np.ndarray
    item_index: dict[int, int]
    item_features: dict[int, dict[str, Any]]
    hot_items: list[int]
    swing_index: dict[int, list[tuple[int, float]]]
    onnx_session: ort.InferenceSession
    milvus_client: MilvusClient
    milvus_collection: str = "item_vectors"

    @property
    def user_columns(self) -> list[str]:
        return self.schema["user_columns"]

    @property
    def item_columns(self) -> list[str]:
        return self.schema["item_columns"]

    @property
    def all_columns(self) -> list[str]:
        return self.schema["all_columns"]

    def encode_user_features(self, user_id: str, feature_map: dict[str, Any]) -> np.ndarray:
        values = []
        for column in self.user_columns:
            raw_value = user_id if column == "user_id" else feature_map.get(column)
            values.append(encode_categorical_value(raw_value, self.schema["vocabs"][column]))
        return np.asarray([values], dtype=np.int64)

    def encode_item_features(self, item_id: int) -> np.ndarray:
        features = self.item_features.get(int(item_id), {})
        values = []
        for column in self.item_columns:
            raw_value = item_id if column == "item_id" else features.get(column)
            values.append(encode_categorical_value(raw_value, self.schema["vocabs"][column]))
        return np.asarray([values], dtype=np.int64)

    def encode_features(
        self,
        user_id: str,
        user_feature_map: dict[str, Any],
        item_id: int,
    ) -> np.ndarray:
        return np.concatenate(
            [
                self.encode_user_features(user_id, user_feature_map),
                self.encode_item_features(item_id),
            ],
            axis=1,
        )

    def price(self, item_id: int) -> float:
        return float(self.item_features.get(int(item_id), {}).get("price", 0.0) or 0.0)

    def vector_for_item(self, item_id: int) -> np.ndarray | None:
        index = self.item_index.get(int(item_id))
        if index is None:
            return None
        return self.item_embeddings[index]

    def search_milvus(self, query_vector: np.ndarray, limit: int) -> list[dict[str, Any]]:
        try:
            results = self.milvus_client.search(
                collection_name=self.milvus_collection,
                data=[np.asarray(query_vector, dtype=np.float32).tolist()],
                limit=limit,
                output_fields=["item_id"],
            )
        except Exception:
            self.milvus_client.load_collection(self.milvus_collection)
            results = self.milvus_client.search(
                collection_name=self.milvus_collection,
                data=[np.asarray(query_vector, dtype=np.float32).tolist()],
                limit=limit,
                output_fields=["item_id"],
            )
        return [
            {"item_id": int(hit["item_id"]), "score": float(hit["distance"])}
            for hit in results[0]
        ]


def _model_root(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(os.getenv("RECSYS_MODEL_ROOT", str(DEFAULT_MODEL_ROOT)))


@lru_cache(maxsize=4)
def _load_bundle(bundle_path_str: str) -> ModelBundle:
    bundle_path = Path(bundle_path_str)
    manifest = json.loads((bundle_path / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((bundle_path / "feature_schema.json").read_text(encoding="utf-8"))
    item_ids = np.load(bundle_path / "item_ids.npy")
    item_embeddings = np.load(bundle_path / "item_embeddings.npy").astype(np.float32)
    item_features_df = pd.read_parquet(bundle_path / "item_features.parquet")
    item_features = {
        int(row["item_id"]): {
            key: value
            for key, value in row.items()
            if key != "item_id"
        }
        for row in item_features_df.to_dict(orient="records")
    }
    swing_df = pd.read_parquet(bundle_path / "swing_similarity.parquet")
    swing_index: dict[int, list[tuple[int, float]]] = {}
    for item_id, group in swing_df.groupby("item_id", sort=False):
        swing_index[int(item_id)] = [
            (int(row.neighbor_item_id), float(row.score))
            for row in group.itertuples(index=False)
        ]

    milvus_uri = str(bundle_path / "milvus.db")
    milvus_client = MilvusClient(uri=milvus_uri)
    milvus_client.load_collection("item_vectors")
    onnx_session = ort.InferenceSession(
        str(bundle_path / "deepfm.onnx"),
        providers=["CPUExecutionProvider"],
    )
    return ModelBundle(
        version=bundle_path.name,
        path=bundle_path,
        manifest=manifest,
        schema=schema,
        item_ids=item_ids,
        item_embeddings=item_embeddings,
        item_index={
            int(item_id): index
            for index, item_id in enumerate(item_ids.tolist())
        },
        item_features=item_features,
        hot_items=[
            int(item_id)
            for item_id in json.loads((bundle_path / "hot_items.json").read_text(encoding="utf-8"))
        ],
        swing_index=swing_index,
        onnx_session=onnx_session,
        milvus_client=milvus_client,
    )


def load_latest_bundle(root: Path | None = None, version: str | None = None) -> ModelBundle:
    model_root = _model_root(root)
    candidates = sorted(
        [
            path
            for path in model_root.iterdir()
            if path.is_dir() and (path / "manifest.json").exists()
        ],
        key=lambda path: ((path / "manifest.json").stat().st_mtime, path.name),
    )
    if not candidates:
        raise FileNotFoundError(f"no model bundle found under {model_root}")
    bundle_path = model_root / version if version else candidates[-1]
    if not bundle_path.exists():
        raise FileNotFoundError(f"model version not found: {bundle_path}")
    return _load_bundle(str(bundle_path.resolve()))


class ModelManager:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _model_root(root)
        self._lock = threading.RLock()
        self._bundle: ModelBundle | None = None
        self.reload()

    @property
    def bundle(self) -> ModelBundle:
        if self._bundle is None:
            raise RuntimeError("model bundle is not loaded")
        return self._bundle

    def reload(self, version: str | None = None) -> ModelBundle:
        with self._lock:
            bundle = load_latest_bundle(self.root, version)
            self._bundle = bundle
            return bundle
