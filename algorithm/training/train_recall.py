"""Train the two-tower recall model.

Usage:
    python -m algorithm.training.train_recall
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from algorithm.common.config_loader import get_config
from algorithm.common.features.schema import FeatureConfig
from algorithm.common.features.transform import save_feature_config
from algorithm.recall.two_tower import TwoTowerModel
from algorithm.training.datasets import RecallDataset, collate_recall


def pairwise_loss(scores: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    # In-batch negative sampling: for each positive sample, the rest of the batch are negatives.
    pos_mask = (labels > 0).float()
    if pos_mask.sum() == 0:
        return F.binary_cross_entropy_with_logits(scores, labels)
    loss = F.binary_cross_entropy_with_logits(scores, labels)
    return loss


def build_feature_config() -> FeatureConfig:
    # FeatureConfig() 默认值已经把 item_id/user_id 调到 1M/2M, 见 schema.DEFAULT_CAT_VOCAB_SIZE.
    # 想覆盖时直接改这里; 训练完会落到 feature_config.json, 推理服务读取.
    return FeatureConfig()


def main() -> None:
    cfg = get_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", default=str(Path(cfg["path"]["processedDataDir"]) / "recall_samples"))
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    fc = build_feature_config()
    if Path(args.samples).exists():
        ds = RecallDataset(args.samples, fc)
    else:
        print(f"[warn] no samples at {args.samples} - exporting random-init model only")
        ds = None

    user_cat = {n: fc.cat_vocab_size[n] for n in fc.user_cat}
    item_cat = {n: fc.cat_vocab_size[n] for n in fc.item_cat}
    model = TwoTowerModel(user_cat, item_cat, len(fc.user_cont), len(fc.item_cont),
                          emb_dim=fc.embedding_dim)

    if ds is not None and len(ds) > 0:
        loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate_recall)
        opt = torch.optim.Adam(model.parameters(), lr=args.lr)
        model.train()
        for epoch in range(args.epochs):
            for step, batch in enumerate(loader):
                scores = model(batch["user_in"], batch["item_in"])
                loss = pairwise_loss(scores, batch["label"])
                opt.zero_grad()
                loss.backward()
                opt.step()
                if step % 100 == 0:
                    print(f"epoch={epoch} step={step} loss={loss.item():.4f}")

    out_dir = Path(cfg["path"]["modelDir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "recall_user_tower.pt")
    save_feature_config(fc, out_dir / "feature_config.json")
    print(f"recall model saved to {out_dir/'recall_user_tower.pt'}")


if __name__ == "__main__":
    main()
