"""Nightly entry: Spark 离线样本 → 双塔/MMoE 训练 → 物品向量发布.

默认按天池数据集 1000 万行上限进行训练; 可通过 --max-rows 覆盖.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAX_ROWS = 10_000_000


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT))
    if res.returncode != 0:
        print(f"[warn] step failed: {' '.join(cmd)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS,
                        help="rec_behavior_log 抽样上限 (默认 10_000_000)")
    parser.add_argument("--epochs-recall", type=int, default=1)
    parser.add_argument("--epochs-ranking", type=int, default=1)
    parser.add_argument("--skip-spark", action="store_true",
                        help="跳过 Spark 任务; 假设 data/processed 已经准备好")
    parser.add_argument("--skip-publish", action="store_true",
                        help="跳过 publish_item_embedding (无 Milvus 时使用)")
    args = parser.parse_args()

    py = sys.executable

    if not args.skip_spark:
        # Spark 步骤
        run([py, "data-pipeline/spark/offline_samples_job.py",
             "--max-rows", str(args.max_rows)])
        run([py, "data-pipeline/spark/popularity_job.py"])
        run([py, "data-pipeline/spark/tag_lbs_index_job.py"])

    run([py, "-m", "algorithm.training.train_recall",
         "--epochs", str(args.epochs_recall)])
    run([py, "-m", "algorithm.training.train_ranking",
         "--epochs", str(args.epochs_ranking)])

    if not args.skip_publish:
        run([py, "-m", "algorithm.training.publish_item_embedding"])


if __name__ == "__main__":
    main()
