"""Train the MMoE ranking model. Mirrors train_recall.py structure."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from algorithm.common.config_loader import get_config
from algorithm.common.features.schema import FeatureConfig
from algorithm.common.features.transform import save_feature_config
from algorithm.ranking.mmoe import MMoERanking
from algorithm.training.datasets import RankingDataset, collate_ranking


def build_feature_config() -> FeatureConfig:
    # 同 train_recall: 使用 DEFAULT_CAT_VOCAB_SIZE 默认 (item_id=2M, user_id=1M).
    return FeatureConfig()


def main() -> None:
    cfg = get_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", default=str(Path(cfg["path"]["processedDataDir"]) / "ranking_samples"))
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    fc = build_feature_config()
    if Path(args.samples).exists():
        ds = RankingDataset(args.samples, fc)
    else:
        print(f"[warn] no samples at {args.samples} - exporting random-init model only")
        ds = None

    user_cat = {n: fc.cat_vocab_size[n] for n in fc.user_cat}
    item_cat = {n: fc.cat_vocab_size[n] for n in fc.item_cat}
    model = MMoERanking(user_cat, item_cat, len(fc.user_cont), len(fc.item_cont), len(fc.cross_cont),
                        emb_dim=fc.embedding_dim)

    if ds is not None and len(ds) > 0:
        loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate_ranking)
        opt = torch.optim.Adam(model.parameters(), lr=args.lr)
        model.train()
        for epoch in range(args.epochs):
            for step, batch in enumerate(loader):
                ctr_logits, cvr_logits = model(batch["user_in"], batch["item_in"], batch["cross_cont"])
                loss = MMoERanking.loss(ctr_logits, cvr_logits, batch["ctr_label"], batch["cvr_label"])
                opt.zero_grad()
                loss.backward()
                opt.step()
                if step % 100 == 0:
                    print(f"epoch={epoch} step={step} loss={loss.item():.4f}")

    out_dir = Path(cfg["path"]["modelDir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "ranking_mmoe.pt")
    save_feature_config(fc, out_dir / "feature_config.json")
    print(f"ranking model saved to {out_dir/'ranking_mmoe.pt'}")


if __name__ == "__main__":
    main()
