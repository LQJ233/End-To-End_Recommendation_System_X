import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from pyspark.sql.functions import col

PROJECT_ROOT = Path("/Users/qj/Item/End-To-End_Recommendation_System_X")
PYSPARK_DIR = PROJECT_ROOT / "offline" / "pyspark"
OUTPUT_ROOT = PROJECT_ROOT / "offline" / "training_output"
sys.path.insert(0, str(PYSPARK_DIR))

from build_ads import build_training_sample  # noqa: E402
from spark_common import create_spark  # noqa: E402
from training.features import encode_categoricals, normalize_price  # noqa: E402
from training.metrics import roc_auc  # noqa: E402
from training.milvus_index import (  # noqa: E402
    create_item_collection,
    insert_item_embeddings,
)
from training.models import DeepFM, TwoTower  # noqa: E402
from training.registry import register_model  # noqa: E402
from training.train import (  # noqa: E402
    ALL_COLUMNS,
    ITEM_COLUMNS,
    USER_COLUMNS,
    export_item_embeddings,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-version", default=None)
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8192)
    return parser.parse_args()


def load_vocabs_from_schema(schema: dict) -> dict[str, dict[int, int]]:
    return {
        column: {int(key): value for key, value in vocab.items()}
        for column, vocab in schema["vocabs"].items()
    }


def latest_bundle(root: Path = OUTPUT_ROOT) -> Path:
    versions = sorted(
        [
            path
            for path in root.iterdir()
            if path.is_dir() and (path / "manifest.json").exists()
        ],
        key=lambda path: ((path / "manifest.json").stat().st_mtime, path.name),
    )
    if not versions:
        raise FileNotFoundError(f"no model bundle found under {root}")
    return versions[-1]


def load_incremental_dataframe(rows: int) -> pd.DataFrame:
    spark = create_spark("incremental_training_data")
    behavior = (
        spark.table("iceberg.dwd.behavior_event")
        .orderBy(col("event_time").desc())
        .limit(rows)
    )
    sample = build_training_sample(
        behavior,
        spark.table("iceberg.dwd.item"),
        spark.table("iceberg.dwd.user"),
        positive_limit=rows,
        negative_limit=rows,
    )
    dataframe = sample.toPandas()
    spark.stop()
    return dataframe


def split_indices(row_count: int) -> tuple[np.ndarray, np.ndarray]:
    indices = np.random.default_rng(42).permutation(row_count)
    split = int(row_count * 0.9)
    return indices[:split], indices[split:]


def train_deepfm_incremental(
    model: DeepFM,
    categorical: np.ndarray,
    numeric: np.ndarray,
    labels: np.ndarray,
    epochs: int,
    batch_size: int,
) -> dict:
    train_index, valid_index = split_indices(len(labels))
    positive_count = int(labels.sum())
    negative_count = int(len(labels) - positive_count)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([negative_count / max(positive_count, 1)], dtype=torch.float32)
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    loader = DataLoader(
        TensorDataset(
            torch.from_numpy(categorical[train_index]),
            torch.from_numpy(numeric[train_index]),
            torch.from_numpy(labels[train_index]),
        ),
        batch_size=batch_size,
        shuffle=True,
    )
    for epoch in range(epochs):
        model.train()
        for categorical_batch, numeric_batch, label_batch in loader:
            optimizer.zero_grad()
            loss = criterion(model(categorical_batch, numeric_batch), label_batch)
            loss.backward()
            optimizer.step()
    model.eval()
    with torch.no_grad():
        logits = model(
            torch.from_numpy(categorical[valid_index]),
            torch.from_numpy(numeric[valid_index]),
        )
        probabilities = torch.sigmoid(logits).numpy()
    return {"auc": round(roc_auc(labels[valid_index], probabilities), 6)}


def train_two_tower_incremental(
    model: TwoTower,
    categorical: np.ndarray,
    labels: np.ndarray,
    epochs: int,
    batch_size: int,
) -> dict:
    train_index, valid_index = split_indices(len(labels))
    user_categorical = categorical[:, : len(USER_COLUMNS)]
    item_categorical = categorical[:, len(USER_COLUMNS):]
    positive_count = int(labels.sum())
    negative_count = int(len(labels) - positive_count)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([negative_count / max(positive_count, 1)], dtype=torch.float32)
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    loader = DataLoader(
        TensorDataset(
            torch.from_numpy(user_categorical[train_index]),
            torch.from_numpy(item_categorical[train_index]),
            torch.from_numpy(labels[train_index]),
        ),
        batch_size=batch_size,
        shuffle=True,
    )
    for epoch in range(epochs):
        model.train()
        for user_batch, item_batch, label_batch in loader:
            optimizer.zero_grad()
            user_vectors, item_vectors = model(user_batch, item_batch)
            logits = (user_vectors * item_vectors).sum(dim=1) * 10.0
            loss = criterion(logits, label_batch)
            loss.backward()
            optimizer.step()
    model.eval()
    with torch.no_grad():
        valid_user, valid_item = model(
            torch.from_numpy(user_categorical[valid_index]),
            torch.from_numpy(item_categorical[valid_index]),
        )
        probabilities = torch.sigmoid((valid_user * valid_item).sum(dim=1) * 10.0).numpy()
    return {"auc": round(roc_auc(labels[valid_index], probabilities), 6)}


def main() -> None:
    args = parse_args()
    base_dir = OUTPUT_ROOT / args.base_version if args.base_version else latest_bundle()
    version = time.strftime("v%Y%m%d-%H%M%S") + "-inc"
    output_dir = OUTPUT_ROOT / version
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"base_version={base_dir.name}")
    print(f"incremental_version={version}")

    schema = json.loads((base_dir / "feature_schema.json").read_text(encoding="utf-8"))
    vocabs = load_vocabs_from_schema(schema)
    for name in [
        "feature_schema.json",
        "item_features.parquet",
        "swing_similarity.parquet",
        "hot_items.json",
    ]:
        shutil.copy2(base_dir / name, output_dir / name)

    dataframe = load_incremental_dataframe(args.rows)
    dataframe.to_parquet(output_dir / "incremental_sample.parquet", index=False)
    categorical = encode_categoricals(dataframe, ALL_COLUMNS, vocabs)
    numeric = normalize_price(dataframe["price"]).reshape(-1, 1)
    labels = dataframe["label"].to_numpy(dtype=np.float32)

    deepfm = DeepFM(
        vocab_sizes=[len(vocabs[column]) + 1 for column in ALL_COLUMNS],
        numeric_dim=1,
        embedding_dim=16,
        hidden_dims=[64, 32],
    )
    deepfm.load_state_dict(torch.load(base_dir / "deepfm.pt", map_location="cpu"))
    deepfm_metrics = train_deepfm_incremental(
        deepfm,
        categorical,
        numeric,
        labels,
        args.epochs,
        args.batch_size,
    )
    torch.save(deepfm.state_dict(), output_dir / "deepfm.pt")
    dummy_categorical = torch.zeros(1, len(ALL_COLUMNS), dtype=torch.long)
    dummy_numeric = torch.zeros(1, 1, dtype=torch.float32)
    torch.onnx.export(
        deepfm,
        (dummy_categorical, dummy_numeric),
        output_dir / "deepfm.onnx",
        dynamo=False,
        input_names=["categorical", "numeric"],
        output_names=["logits"],
        dynamic_axes={
            "categorical": {0: "batch"},
            "numeric": {0: "batch"},
            "logits": {0: "batch"},
        },
        opset_version=18,
    )

    two_tower = TwoTower(
        user_vocab_sizes=[len(vocabs[column]) + 1 for column in USER_COLUMNS],
        item_vocab_sizes=[len(vocabs[column]) + 1 for column in ITEM_COLUMNS],
        embedding_dim=32,
    )
    two_tower.load_state_dict(torch.load(base_dir / "two_tower.pt", map_location="cpu"))
    two_tower_metrics = train_two_tower_incremental(
        two_tower,
        categorical,
        labels,
        args.epochs,
        args.batch_size,
    )
    torch.save(two_tower.state_dict(), output_dir / "two_tower.pt")

    item_features = pd.read_parquet(output_dir / "item_features.parquet")
    item_vocabs = {column: vocabs[column] for column in ITEM_COLUMNS}
    item_ids, item_embeddings = export_item_embeddings(
        two_tower,
        item_features,
        item_vocabs,
        output_dir,
        max_items=len(item_features),
    )
    milvus_uri = str(output_dir / "milvus.db")
    create_item_collection(milvus_uri, dimension=item_embeddings.shape[1])
    indexed = insert_item_embeddings(
        milvus_uri,
        "item_vectors",
        item_ids.tolist(),
        item_embeddings,
    )

    manifest = {
        "version": version,
        "base_version": base_dir.name,
        "incremental": True,
        "training_rows": len(dataframe),
        "positive_rows": int(labels.sum()),
        "negative_rows": int(len(labels) - labels.sum()),
        "deepfm": deepfm_metrics,
        "two_tower": two_tower_metrics,
        "milvus_items": indexed,
        "milvus_uri": milvus_uri,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    register_model("deepfm", version, str(output_dir / "deepfm.onnx"), deepfm_metrics)
    register_model("two_tower", version, str(output_dir / "two_tower.pt"), two_tower_metrics)
    register_model(
        "swing",
        version,
        str(output_dir / "swing_similarity.parquet"),
        {"base_version": base_dir.name, "incremental": True},
    )
    register_model(
        "milvus",
        version,
        milvus_uri,
        {"items": indexed, "base_version": base_dir.name, "incremental": True},
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
