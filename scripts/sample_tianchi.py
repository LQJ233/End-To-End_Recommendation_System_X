"""从天池 user.csv 抽样到一个小数据集, 用于本地快速调试.

策略: 随机抽 N 个 user_id, 把这些用户的全部行为保留下来. 这样能保留
"用户级别"的连续行为, 训练样本更真实.

用法:
    python scripts/sample_tianchi.py --users 5000

输出:
    data/raw/tianchi_mobile_recommend_train_user_sample.csv
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithm.common.config_loader import get_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=5000, help="抽取的用户数")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--input", default=None, help="输入 csv 路径 (默认 data/raw/tianchi_mobile_recommend_train_user.csv)")
    parser.add_argument("--output", default=None, help="输出 csv 路径 (默认 ..._sample.csv)")
    args = parser.parse_args()

    raw_dir = Path(get_config()["path"]["rawDataDir"])
    in_path = Path(args.input) if args.input else raw_dir / "tianchi_mobile_recommend_train_user.csv"
    out_path = Path(args.output) if args.output else raw_dir / "tianchi_mobile_recommend_train_user_sample.csv"

    if not in_path.exists():
        sys.exit(f"input not found: {in_path}")

    random.seed(args.seed)

    # 第一遍: 收集所有 user_id
    print(f"[1/2] scanning {in_path} for user_ids")
    users: set[str] = set()
    with in_path.open("r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        header = next(reader, None)
        for row in reader:
            if row:
                users.add(row[0])
    print(f"  found {len(users):,} distinct users")

    keep = set(random.sample(sorted(users), min(args.users, len(users))))
    print(f"  keeping {len(keep):,} users")

    # 第二遍: 输出保留用户的所有行为
    print(f"[2/2] writing {out_path}")
    written = 0
    with in_path.open("r", encoding="utf-8") as fp_in, \
            out_path.open("w", encoding="utf-8", newline="") as fp_out:
        reader = csv.reader(fp_in)
        writer = csv.writer(fp_out)
        header = next(reader)
        writer.writerow(header)
        for row in reader:
            if row and row[0] in keep:
                writer.writerow(row)
                written += 1
                if written % 100_000 == 0:
                    print(f"  written {written:,}")
    print(f"done. {written:,} rows -> {out_path}")
    print(f"将该文件改名覆盖原 csv 后运行:")
    print(f"  python scripts/import_raw_data.py --max-rows {written}")


if __name__ == "__main__":
    main()
