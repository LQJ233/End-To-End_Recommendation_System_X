"""线程池隔离配置.

为什么要拆两个池:
  - recall_io  : 多路召回都是 I/O 等 (Redis + Milvus), 并发等待为主, 池可以开大;
  - ranking_cpu: MMoE forward 是 CPU 密集 (尤其没用 GPU 时), 池要小到核数附近,
                 否则线程切换反而降低吞吐.

两个池完全隔离, 即使 Milvus 卡死也只影响 recall_io, ranking_cpu 仍能给上一次
召回结果做排序兜底.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


# I/O 池: 服务 N 个并发请求 * 4 路召回 = 4N 个并发等待
RECALL_IO_WORKERS = _env_int("RECSYS_RECALL_IO_WORKERS", 32)
# CPU 池: 物理核数附近, 避免线程切换抢锁
RANKING_CPU_WORKERS = _env_int("RECSYS_RANKING_CPU_WORKERS", max(2, os.cpu_count() or 4))
# 单请求总超时 (秒), 由 service 主流程 wait_for
REQUEST_TIMEOUT_SEC = float(os.environ.get("RECSYS_REQUEST_TIMEOUT_SEC", "2.5"))


recall_io_pool = ThreadPoolExecutor(max_workers=RECALL_IO_WORKERS, thread_name_prefix="recall-io")
ranking_cpu_pool = ThreadPoolExecutor(max_workers=RANKING_CPU_WORKERS, thread_name_prefix="rank-cpu")


def shutdown() -> None:
    recall_io_pool.shutdown(wait=False, cancel_futures=True)
    ranking_cpu_pool.shutdown(wait=False, cancel_futures=True)
