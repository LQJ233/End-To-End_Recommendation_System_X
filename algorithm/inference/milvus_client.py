"""Best-effort Milvus client for vector recall.

If pymilvus or the Milvus server is unavailable, ``available()`` returns False
and the caller is expected to fall back to other recall channels.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from algorithm.common.config_loader import get_config


class MilvusClient:
    def __init__(self):
        self._ok = False
        self._coll = None
        try:
            from pymilvus import Collection, connections, utility  # type: ignore
            cfg = get_config()["milvus"]
            connections.connect(alias="default", host=cfg["host"], port=str(cfg["port"]))
            name = cfg["collection"]
            if utility.has_collection(name):
                self._coll = Collection(name)
                self._coll.load()
                self._ok = True
        except Exception:
            self._ok = False

    def available(self) -> bool:
        return self._ok

    def search(self, user_vector: np.ndarray, top_k: int = 500) -> List[Tuple[str, float]]:
        if not self._ok or self._coll is None:
            return []
        try:
            vec = user_vector.astype("float32").tolist()
            res = self._coll.search(
                data=[vec],
                anns_field="vector",
                param={"metric_type": "COSINE", "params": {"ef": 256}},
                limit=top_k,
                output_fields=["item_id"],
            )
            out: List[Tuple[str, float]] = []
            for hit in res[0]:
                out.append((str(hit.entity.get("item_id")), float(hit.distance)))
            return out
        except Exception:
            return []
