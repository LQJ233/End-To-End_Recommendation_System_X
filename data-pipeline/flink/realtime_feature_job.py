"""PyFlink job: consume user_behavior_log Kafka topic and update Redis features.

Writes:
  - feature:user:click_seq:{userId}        (LPUSH, capped at 50)
  - feature:user:cart_seq:{userId}
  - feature:user:purchase_seq:{userId}
  - feature:user:tag_pref:{userId}         (ZINCRBY based on behaviorType weight)
  - feature:user:last_geo:{userId}         (SET when client provides geohash)
  - feature:user:{userId}                  (HINCRBY counters, behaviorCnt1h, etc.)

Run with:
  python data-pipeline/flink/realtime_feature_job.py
"""
from __future__ import annotations

import json
import time
from typing import Dict

import redis
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from algorithm.common.config_loader import get_config

BEHAVIOR_WEIGHT = {0: 0.0, 1: 1.0, 2: 2.0, 3: 3.0, 4: 5.0}
SEQ_KIND_BY_BEHAVIOR = {1: "click_seq", 3: "cart_seq", 4: "purchase_seq"}
SEQ_MAX_LEN = 50

_redis = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        cfg = get_config()["redis"]
        _redis = redis.Redis(
            host=cfg["host"], port=int(cfg["port"]),
            db=int(cfg.get("database", 0)),
            password=cfg.get("password") or None,
            decode_responses=True,
        )
    return _redis


def update_features(message: str) -> str:
    try:
        evt: Dict = json.loads(message)
    except Exception:
        return "skip:bad_json"
    user_id = evt.get("userId")
    item_id = evt.get("itemId")
    behavior = int(evt.get("behaviorType", -1))
    if not user_id or not item_id or behavior < 0:
        return "skip:missing"

    r = _get_redis()

    user_hash_key = f"feature:user:{user_id}"
    r.hincrby(user_hash_key, f"behavior_cnt_{behavior}", 1)
    r.hset(user_hash_key, "last_event_ts", int(evt.get("timestamp", time.time() * 1000)))
    r.expire(user_hash_key, 7 * 86400)

    seq_kind = SEQ_KIND_BY_BEHAVIOR.get(behavior)
    if seq_kind:
        seq_key = f"feature:user:{seq_kind}:{user_id}"
        r.lpush(seq_key, item_id)
        r.ltrim(seq_key, 0, SEQ_MAX_LEN - 1)
        r.expire(seq_key, 30 * 86400 if behavior == 4 else 7 * 86400)

    geohash = evt.get("userGeohash") or evt.get("geohash")
    if geohash:
        r.set(f"feature:user:last_geo:{user_id}", geohash, ex=7 * 86400)

    weight = BEHAVIOR_WEIGHT.get(behavior, 0.0)
    tag_type = evt.get("itemCategory")
    if weight > 0 and tag_type:
        zkey = f"feature:user:tag_pref:{user_id}"
        r.zincrby(zkey, weight, f"item_category:{tag_type}")
        r.expire(zkey, 7 * 86400)

    return "ok"


def main() -> None:
    cfg = get_config()
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    source = (
        KafkaSource.builder()
        .set_bootstrap_servers(cfg["kafka"]["bootstrapServers"])
        .set_topics(cfg["kafka"]["behaviorTopic"])
        .set_group_id(cfg["kafka"].get("consumerGroup", "End-To-End_Recommendation_System_X-flink"))
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )
    ds = env.from_source(source, WatermarkStrategy.no_watermarks(), "user_behavior_source")
    ds.map(update_features, output_type=Types.STRING()).print()
    env.execute("end_to_end_recommendation_system_x_realtime_feature")


if __name__ == "__main__":
    main()
