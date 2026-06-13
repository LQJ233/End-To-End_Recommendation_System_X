"""Export every biz_item to Milvus as a vector from the item tower."""
from __future__ import annotations

import sys
from pathlib import Path

import pymysql
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from algorithm.common.config_loader import get_config
from algorithm.common.features.schema import FeatureConfig
from algorithm.common.features.transform import build_item_input, load_feature_config
from algorithm.recall.two_tower import TwoTowerModel


def load_items() -> list[dict]:
    cfg = get_config()["mysql"]
    conn = pymysql.connect(host=cfg["host"], port=int(cfg["port"]),
                           user=cfg["username"], password=cfg["password"],
                           database=cfg["database"], charset="utf8mb4",
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_id, item_category, brand, price_bucket FROM biz_item WHERE status=1")
            return cur.fetchall()
    finally:
        conn.close()


def build_model(fc: FeatureConfig) -> TwoTowerModel:
    user_cat = {n: fc.cat_vocab_size.get(n, 100_000) for n in fc.user_cat}
    item_cat = {n: fc.cat_vocab_size.get(n, 100_000) for n in fc.item_cat}
    model = TwoTowerModel(user_cat, item_cat, len(fc.user_cont), len(fc.item_cont),
                          emb_dim=fc.embedding_dim)
    return model


def write_milvus(items: list[dict], vectors, model_version: str) -> None:
    try:
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
    except Exception as e:
        print(f"[warn] pymilvus unavailable: {e}, skip milvus write")
        return
    cfg = get_config()["milvus"]
    connections.connect(host=cfg["host"], port=str(cfg["port"]))
    name = cfg["collection"]
    dim = vectors.shape[1]
    if not utility.has_collection(name):
        schema = CollectionSchema(fields=[
            FieldSchema(name="item_id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="item_category", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="model_version", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="updated_at", dtype=DataType.INT64),
        ])
        Collection(name=name, schema=schema)
    coll = Collection(name)
    coll.delete(expr="item_id != ''")
    import time
    coll.insert([
        [str(it["item_id"]) for it in items],
        vectors.tolist(),
        [str(it.get("item_category") or "") for it in items],
        [model_version for _ in items],
        [int(time.time() * 1000) for _ in items],
    ])
    coll.flush()
    if not coll.indexes:
        coll.create_index("vector", {"index_type": cfg.get("indexType", "HNSW"),
                                     "metric_type": cfg.get("metricType", "COSINE"),
                                     "params": {"M": 16, "efConstruction": 200}})
    coll.load()


def main() -> None:
    cfg = get_config()
    model_dir = Path(cfg["path"]["modelDir"])
    fc_path = model_dir / "feature_config.json"
    if not fc_path.exists():
        print(f"[error] missing {fc_path}; run train_recall first")
        return
    fc = load_feature_config(fc_path)
    model = build_model(fc)
    recall_path = model_dir / "recall_user_tower.pt"
    if recall_path.exists():
        model.load_state_dict(torch.load(recall_path, map_location="cpu"))
    model.eval()

    items = load_items()
    if not items:
        print("no items in biz_item; nothing to publish")
        return
    item_cat_tensors = {n: [] for n in fc.item_cat}
    item_cont = []
    for it in items:
        ii = build_item_input(it, fc)
        for n in fc.item_cat:
            item_cat_tensors[n].append(ii["cat"][n])
        item_cont.append(ii["cont"])
    cats = {n: torch.tensor(vs, dtype=torch.long) for n, vs in item_cat_tensors.items()}
    cont = torch.tensor(item_cont, dtype=torch.float32)
    with torch.no_grad():
        vectors = model.encode_item({"cat": cats, "cont": cont}).cpu().numpy()
    write_milvus(items, vectors, cfg["model"].get("modelVersion", "20260526_0000"))
    print(f"published {len(items)} item vectors to milvus")


if __name__ == "__main__":
    main()
