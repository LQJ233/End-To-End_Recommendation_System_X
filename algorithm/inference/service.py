"""核心编排: 特征读取 -> 召回 -> 排序.

高并发设计要点:
  1. 召回 4 通道 (vector/lbs/tag/cache) 在 recall_io_pool 上并发, 任意一路超时
     都不会拖垮整体, 但会被记录到 recallDebug;
  2. 排序在 ranking_cpu_pool 上跑, 与召回 I/O 物理隔离;
  3. 单请求总超时 REQUEST_TIMEOUT_SEC, 超时返回热门商品兜底.

注意: 该模块只在 inference service 中使用; 训练相关代码不会经过这里.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import Future, TimeoutError as FutureTimeout, wait
from typing import Any, Callable, Dict, List

import torch

from algorithm.common.config_loader import get_config
from algorithm.common.features.transform import build_user_input, build_item_input
from algorithm.inference import recall_runner, redis_client
from algorithm.inference.executors import (
    REQUEST_TIMEOUT_SEC, ranking_cpu_pool, recall_io_pool,
)
from algorithm.inference.metrics import (
    CHANNEL_LATENCY_MS, CHANNEL_SIZE, FALLBACK_TOTAL, RANK_LATENCY_MS,
)
from algorithm.inference.milvus_client import MilvusClient
from algorithm.inference.model_registry import ModelRegistry


logger = logging.getLogger("inference.service")


class InferenceService:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.milvus = MilvusClient()

    def health(self) -> Dict[str, Any]:
        return {
            "status": "UP",
            "modelVersion": self.registry.model_version,
            "recallLoaded": self.registry.recall_loaded,
            "rankingLoaded": self.registry.ranking_loaded,
        }

    # ------------------------------------------------------------------
    def recommend(self, req: Dict[str, Any]) -> Dict[str, Any]:
        cfg = get_config()
        t0 = time.time()
        feature_snapshot_time = int(t0 * 1000)

        user_id = req["userId"]
        scene = req.get("scene", "home")
        exclude = set(req.get("excludeItemIds") or [])
        recall_size = int(req.get("recallSize") or cfg["recommendation"].get("recallSize", 500))
        options = req.get("recallOptions") or {}

        # ---- 1. 用户特征 (一次 pipeline 一次 RTT 拿完 6 个 key) ----
        seq_len = self.registry.feature_config.seq_max_len
        bundle = redis_client.read_user_bundle(user_id, seq_len=seq_len, tag_top_n=10)
        raw_user_features = dict(bundle.features)
        raw_user_features.setdefault("user_id", user_id)
        raw_user_features["click_seq"] = bundle.click_seq
        raw_user_features["cart_seq"] = bundle.cart_seq
        raw_user_features["purchase_seq"] = bundle.purchase_seq
        # 把 geohash / tag_pref 透传给召回通道, 避免它们再读一次 Redis
        if bundle.last_geo:
            raw_user_features["last_geo"] = bundle.last_geo
        raw_user_features["_tag_pref"] = bundle.tag_pref

        user_in = build_user_input(user_id, raw_user_features, self.registry.feature_config)
        user_tensor = self._user_input_to_tensors(user_in)

        # ---- 2. 多路召回并发 (recall_io_pool) ----
        channels: Dict[str, Dict[str, float]] = {}
        per_channel_deadline = max(0.1, REQUEST_TIMEOUT_SEC * 0.7)

        futures: Dict[str, Future] = {}
        if options.get("enableVectorRecall", True):
            futures["vector"] = recall_io_pool.submit(self._run_vector_recall, user_tensor)
        if options.get("enableLbsRecall", True):
            futures["lbs"] = recall_io_pool.submit(
                recall_runner.lbs_recall, user_id, bundle.last_geo)
        if options.get("enableTagRecall", True):
            futures["tag"] = recall_io_pool.submit(
                recall_runner.tag_recall, user_id, bundle.tag_pref)
        futures["cache"] = recall_io_pool.submit(recall_runner.cache_recall, user_id)

        channel_start = {n: time.time() for n in futures}
        done, not_done = wait(futures.values(), timeout=per_channel_deadline)
        for name, fut in futures.items():
            if fut in done:
                try:
                    channels[name] = fut.result() or {}
                except Exception as e:
                    logger.warning("recall channel %s failed: %s", name, e)
                    channels[name] = {}
            else:
                logger.warning("recall channel %s timed out (>%.2fs)", name, per_channel_deadline)
                fut.cancel()
                channels[name] = {}
            CHANNEL_SIZE.labels(channel=name).observe(len(channels[name]))
            CHANNEL_LATENCY_MS.labels(channel=name).observe(
                (time.time() - channel_start[name]) * 1000.0)

        merged = recall_runner.merge(channels)
        if not merged:
            FALLBACK_TOTAL.labels(reason="recall_empty").inc()
            # 全部召回都没数据 -> 热门兜底
            merged = {iid: {"channels": ["hot"], "score": s}
                      for iid, s in recall_runner.hot_recall(recall_size).items()}

        merged = {iid: row for iid, row in merged.items() if iid not in exclude}

        # ---- 3. 排序 (ranking_cpu_pool, 受总剩余时间约束) ----
        elapsed = time.time() - t0
        rank_budget = max(0.05, REQUEST_TIMEOUT_SEC - elapsed)
        rank_start = time.time()
        try:
            rank_future = ranking_cpu_pool.submit(self._rank, user_tensor, merged)
            ranked = rank_future.result(timeout=rank_budget)
        except FutureTimeout:
            logger.warning("ranking timed out budget=%.2fs", rank_budget)
            FALLBACK_TOTAL.labels(reason="ranking_timeout").inc()
            ranked = self._rank_by_recall_score(merged)
        except Exception as e:
            logger.warning("ranking failed: %s", e)
            FALLBACK_TOTAL.labels(reason="ranking_failed").inc()
            ranked = self._rank_by_recall_score(merged)
        RANK_LATENCY_MS.observe((time.time() - rank_start) * 1000.0)

        debug = {
            "vectorRecallSize": len(channels.get("vector", {})),
            "lbsRecallSize": len(channels.get("lbs", {})),
            "tagRecallSize": len(channels.get("tag", {})),
            "cacheRecallSize": len(channels.get("cache", {})),
            "mergedSize": len(merged),
            "latencyMs": int((time.time() - t0) * 1000),
        }
        return {
            "modelVersion": self.registry.model_version,
            "featureSnapshotTime": feature_snapshot_time,
            "recallDebug": debug,
            "items": ranked[:recall_size],
        }

    # ------------------------------------------------------------------
    def _run_vector_recall(self, user_tensor: Dict[str, Any]) -> Dict[str, float]:
        if not self.milvus.available():
            return {}
        user_vec = self._user_vector(user_tensor)
        if user_vec is None:
            return {}
        top_k = int(get_config()["recommendation"].get("vectorRecallSize", 500))
        return recall_runner.vector_recall(self.milvus.search(user_vec, top_k))

    def _rank_by_recall_score(self, merged: Dict[str, dict]) -> List[Dict[str, Any]]:
        items = [
            {"itemId": iid, "recallChannels": row["channels"],
             "recallScore": float(row["score"]),
             "ctr": 0.0, "cvr": 0.0, "rankScore": float(row["score"])}
            for iid, row in merged.items()
        ]
        items.sort(key=lambda r: r["rankScore"], reverse=True)
        return items

    def _user_input_to_tensors(self, user_in: Dict[str, Any]) -> Dict[str, Any]:
        cat = {k: torch.tensor([v], dtype=torch.long) for k, v in user_in["cat"].items()}
        cont = torch.tensor([user_in["cont"]], dtype=torch.float32)
        seqs = {
            "click_seq": torch.tensor([user_in["click_seq"]], dtype=torch.long),
            "cart_seq": torch.tensor([user_in["cart_seq"]], dtype=torch.long),
            "purchase_seq": torch.tensor([user_in["purchase_seq"]], dtype=torch.long),
        }
        return {"cat": cat, "cont": cont, "seqs": seqs}

    def _user_vector(self, user_in: Dict[str, Any]):
        if self.registry.recall_model is None:
            return None
        with torch.no_grad():
            try:
                return self.registry.recall_model.encode_user(user_in).cpu().numpy()[0]
            except Exception:
                return None

    def _rank(self, user_tensor: Dict[str, Any], merged: Dict[str, dict]) -> List[Dict[str, Any]]:
        items_list = list(merged.items())
        if not items_list:
            return []
        ranker = self.registry.ranking_model
        fc = self.registry.feature_config
        if ranker is None:
            return self._rank_by_recall_score(merged)

        batch_user_cat = {k: v.expand(len(items_list), *v.shape[1:]) for k, v in user_tensor["cat"].items()}
        batch_user_cont = user_tensor["cont"].expand(len(items_list), -1)

        item_cat: Dict[str, List[int]] = {n: [] for n in fc.item_cat}
        item_cont: List[List[float]] = []
        for iid, _row in items_list:
            iin = build_item_input({"item_id": iid}, fc)
            for n in fc.item_cat:
                item_cat[n].append(iin["cat"][n])
            item_cont.append(iin["cont"])
        item_cat_tensors = {k: torch.tensor(v, dtype=torch.long) for k, v in item_cat.items()}
        item_cont_tensor = torch.tensor(item_cont, dtype=torch.float32)
        cross_cont_tensor = torch.zeros(len(items_list), len(fc.cross_cont), dtype=torch.float32)

        with torch.no_grad():
            ctr_logits, cvr_logits = ranker(
                {"cat": batch_user_cat, "cont": batch_user_cont},
                {"cat": item_cat_tensors, "cont": item_cont_tensor},
                cross_cont_tensor,
            )
            cfg_rec = get_config()["recommendation"]
            score = ranker.rank_score(
                ctr_logits, cvr_logits,
                ctr_weight=float(cfg_rec.get("rankScoreCtrWeight", 0.7)),
                cvr_weight=float(cfg_rec.get("rankScoreCvrWeight", 0.3)),
            )
        ctr_p = torch.sigmoid(ctr_logits).cpu().numpy()
        cvr_p = torch.sigmoid(cvr_logits).cpu().numpy()
        score_np = score.cpu().numpy()

        ranked: List[Dict[str, Any]] = []
        for idx, (iid, row) in enumerate(items_list):
            ranked.append({
                "itemId": iid,
                "recallChannels": row["channels"],
                "recallScore": float(row["score"]),
                "ctr": float(ctr_p[idx]),
                "cvr": float(cvr_p[idx]),
                "rankScore": float(score_np[idx]),
            })
        ranked.sort(key=lambda r: r["rankScore"], reverse=True)
        return ranked
