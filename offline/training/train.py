import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = Path("/Users/qj/Item/End-To-End_Recommendation_System_X")
PYSPARK_DIR = PROJECT_ROOT / "offline" / "pyspark"
OUTPUT_ROOT = PROJECT_ROOT / "offline" / "training_output"
sys.path.insert(0, str(PYSPARK_DIR))

from spark_common import create_spark  # noqa: E402
from training.features import build_vocab, encode_categoricals, normalize_price  # noqa: E402
from training.metrics import roc_auc  # noqa: E402
from training.milvus_index import (  # noqa: E402
    create_item_collection,
    insert_item_embeddings,
)
from training.models import DeepFM, TwoTower  # noqa: E402
from training.registry import register_model  # noqa: E402
from training.swing import build_swing_similarity  # noqa: E402


USER_COLUMNS = [
    "user_id",
    "cms_segid",
    "cms_group_id",
    "final_gender_code",
    "age_level",
    "pvalue_level",
    "shopping_level",
    "occupation",
    "new_user_class_level",
]
ITEM_COLUMNS = [
    "item_id",
    "category_id",
    "brand_id",
    "campaign_id",
    "customer_id",
]
ALL_COLUMNS = USER_COLUMNS + ITEM_COLUMNS
TRAINING_ROWS = 1_000_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--max-milvus-items", type=int, default=100_000)
    return parser.parse_args()


def write_status(output_dir: Path, stage: str, **details) -> None:
    payload = {
        "stage": stage,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        **details,
    }
    (output_dir / "training_status.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[training] {json.dumps(payload, ensure_ascii=False)}", flush=True)


def load_training_data() -> pd.DataFrame:
    spark = create_spark("train_recommendation_models_1m")
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
    dataframe = spark.table("iceberg.ads.training_sample").limit(TRAINING_ROWS)
    rows = dataframe.count()
    if rows != TRAINING_ROWS:
        raise RuntimeError(f"expected {TRAINING_ROWS} rows, got {rows}")
    pandas_df = dataframe.toPandas()
    spark.stop()
    return pandas_df


def split_indices(row_count: int, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    indices = np.random.default_rng(seed).permutation(row_count)
    split = int(row_count * 0.9)
    return indices[:split], indices[split:]


def train_deepfm(
    categorical: np.ndarray,
    numeric: np.ndarray,
    labels: np.ndarray,
    vocabs: dict[str, dict[int, int]],
    output_dir: Path,
    epochs: int,
    batch_size: int,
) -> dict:
    train_index, valid_index = split_indices(len(labels))
    model = DeepFM(
        vocab_sizes=[len(vocab) + 1 for vocab in vocabs.values()],
        numeric_dim=numeric.shape[1],
        embedding_dim=16,
        hidden_dims=[64, 32],
    )
    positive_count = int(labels.sum())
    negative_count = int(len(labels) - positive_count)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([negative_count / max(positive_count, 1)], dtype=torch.float32)
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
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
        total_loss = 0.0
        samples = 0
        for categorical_batch, numeric_batch, label_batch in loader:
            optimizer.zero_grad()
            logits = model(categorical_batch, numeric_batch)
            loss = criterion(logits, label_batch)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(label_batch)
            samples += len(label_batch)
        print(
            f"[deepfm] epoch={epoch + 1}/{epochs} loss={total_loss / samples:.6f}",
            flush=True,
        )

    model.eval()
    with torch.no_grad():
        valid_logits = model(
            torch.from_numpy(categorical[valid_index]),
            torch.from_numpy(numeric[valid_index]),
        )
        valid_probabilities = torch.sigmoid(valid_logits).numpy()
    metrics = {"auc": round(roc_auc(labels[valid_index], valid_probabilities), 6)}

    torch.save(model.state_dict(), output_dir / "deepfm.pt")
    dummy_categorical = torch.zeros(1, len(ALL_COLUMNS), dtype=torch.long)
    dummy_numeric = torch.zeros(1, numeric.shape[1], dtype=torch.float32)
    traced = torch.jit.trace(model, (dummy_categorical, dummy_numeric))
    traced.save(str(output_dir / "deepfm_traced.pt"))
    try:
        torch.onnx.export(
            model,
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
        metrics["onnx_export"] = "ok"
    except Exception as exc:
        metrics["onnx_export"] = f"skipped: {type(exc).__name__}: {exc}"
    return metrics


def train_two_tower(
    categorical: np.ndarray,
    labels: np.ndarray,
    vocabs: dict[str, dict[int, int]],
    output_dir: Path,
    epochs: int,
    batch_size: int,
) -> dict:
    train_index, valid_index = split_indices(len(labels))
    user_categorical = categorical[:, : len(USER_COLUMNS)]
    item_categorical = categorical[:, len(USER_COLUMNS):]
    model = TwoTower(
        user_vocab_sizes=[len(vocabs[column]) + 1 for column in USER_COLUMNS],
        item_vocab_sizes=[len(vocabs[column]) + 1 for column in ITEM_COLUMNS],
        embedding_dim=32,
    )
    positive_count = int(labels.sum())
    negative_count = int(len(labels) - positive_count)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([negative_count / max(positive_count, 1)], dtype=torch.float32)
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
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
        total_loss = 0.0
        samples = 0
        for user_batch, item_batch, label_batch in loader:
            optimizer.zero_grad()
            user_vectors, item_vectors = model(user_batch, item_batch)
            logits = (user_vectors * item_vectors).sum(dim=1) * 10.0
            loss = criterion(logits, label_batch)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(label_batch)
            samples += len(label_batch)
        print(
            f"[two_tower] epoch={epoch + 1}/{epochs} loss={total_loss / samples:.6f}",
            flush=True,
        )

    model.eval()
    with torch.no_grad():
        valid_user, valid_item = model(
            torch.from_numpy(user_categorical[valid_index]),
            torch.from_numpy(item_categorical[valid_index]),
        )
        valid_probabilities = torch.sigmoid((valid_user * valid_item).sum(dim=1) * 10.0).numpy()

    torch.save(model.state_dict(), output_dir / "two_tower.pt")
    return {"auc": round(roc_auc(labels[valid_index], valid_probabilities), 6)}


def export_item_embeddings(
    model: TwoTower,
    dataframe: pd.DataFrame,
    item_vocabs: dict[str, dict[int, int]],
    output_dir: Path,
    max_items: int,
) -> tuple[np.ndarray, np.ndarray]:
    item_catalog = (
        dataframe[ITEM_COLUMNS]
        .drop_duplicates(subset=["item_id"])
        .head(max_items)
        .reset_index(drop=True)
    )
    encoded = encode_categoricals(item_catalog, ITEM_COLUMNS, item_vocabs)
    item_ids = item_catalog["item_id"].to_numpy(dtype=np.int64)
    vectors = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(encoded), 4096):
            _, item_vectors = model(
                torch.zeros(min(4096, len(encoded) - start), len(USER_COLUMNS), dtype=torch.long),
                torch.from_numpy(encoded[start:start + 4096]),
            )
            vectors.append(item_vectors.numpy())
    item_embeddings = np.concatenate(vectors, axis=0)
    np.save(output_dir / "item_ids.npy", item_ids)
    np.save(output_dir / "item_embeddings.npy", item_embeddings)
    return item_ids, item_embeddings


def main() -> None:
    args = parse_args()
    version = time.strftime("v%Y%m%d-%H%M%S")
    output_dir = OUTPUT_ROOT / version
    output_dir.mkdir(parents=True, exist_ok=True)

    write_status(output_dir, "loading_data", version=version, rows=TRAINING_ROWS)
    dataframe = load_training_data()
    dataframe.to_parquet(output_dir / "training_sample.parquet", index=False)

    write_status(output_dir, "building_features", rows=len(dataframe))
    vocabs = {column: build_vocab(dataframe[column]) for column in ALL_COLUMNS}
    categorical = encode_categoricals(dataframe, ALL_COLUMNS, vocabs)
    numeric = normalize_price(dataframe["price"]).reshape(-1, 1)
    labels = dataframe["label"].to_numpy(dtype=np.float32)
    item_features = (
        dataframe[ITEM_COLUMNS]
        .drop_duplicates(subset=["item_id"])
        .sort_values("item_id")
        .reset_index(drop=True)
    )
    item_features.to_parquet(output_dir / "item_features.parquet", index=False)
    (output_dir / "feature_schema.json").write_text(
        json.dumps(
            {
                "user_columns": USER_COLUMNS,
                "item_columns": ITEM_COLUMNS,
                "all_columns": ALL_COLUMNS,
                "vocabs": {
                    column: {str(key): value for key, value in vocab.items()}
                    for column, vocab in vocabs.items()
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    write_status(output_dir, "training_deepfm", epoch=args.epochs)
    deepfm_metrics = train_deepfm(
        categorical,
        numeric,
        labels,
        vocabs,
        output_dir,
        args.epochs,
        args.batch_size,
    )

    write_status(output_dir, "training_two_tower", epoch=args.epochs)
    two_tower_metrics = train_two_tower(
        categorical,
        labels,
        vocabs,
        output_dir,
        args.epochs,
        args.batch_size,
    )

    write_status(output_dir, "building_swing")
    clicks = dataframe.loc[dataframe["label"] == 1, ["user_id", "item_id"]]
    swing = build_swing_similarity(clicks, max_items_per_user=10, max_neighbors=50)
    swing.to_parquet(output_dir / "swing_similarity.parquet", index=False)

    hot_items = (
        dataframe.loc[dataframe["label"] == 1, "item_id"]
        .value_counts()
        .head(5000)
        .index.astype(int)
        .tolist()
    )
    (output_dir / "hot_items.json").write_text(
        json.dumps(hot_items, ensure_ascii=False),
        encoding="utf-8",
    )

    write_status(output_dir, "building_milvus")
    model = TwoTower(
        user_vocab_sizes=[len(vocabs[column]) + 1 for column in USER_COLUMNS],
        item_vocab_sizes=[len(vocabs[column]) + 1 for column in ITEM_COLUMNS],
        embedding_dim=32,
    )
    model.load_state_dict(torch.load(output_dir / "two_tower.pt", map_location="cpu"))
    item_ids, item_embeddings = export_item_embeddings(
        model,
        dataframe,
        {column: vocabs[column] for column in ITEM_COLUMNS},
        output_dir,
        args.max_milvus_items,
    )
    milvus_uri = str(output_dir / "milvus.db")
    create_item_collection(milvus_uri, dimension=item_embeddings.shape[1])
    indexed = insert_item_embeddings(milvus_uri, "item_vectors", item_ids.tolist(), item_embeddings)

    manifest = {
        "version": version,
        "training_rows": len(dataframe),
        "positive_rows": int(labels.sum()),
        "negative_rows": int(len(labels) - labels.sum()),
        "user_count": int(dataframe["user_id"].nunique()),
        "item_count": int(dataframe["item_id"].nunique()),
        "deepfm": deepfm_metrics,
        "two_tower": two_tower_metrics,
        "swing_rows": len(swing),
        "hot_items": len(hot_items),
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
        {"rows": len(swing)},
    )
    register_model(
        "milvus",
        version,
        milvus_uri,
        {"items": indexed, "dimension": int(item_embeddings.shape[1])},
    )

    write_status(output_dir, "completed", manifest=manifest)


if __name__ == "__main__":
    main()
