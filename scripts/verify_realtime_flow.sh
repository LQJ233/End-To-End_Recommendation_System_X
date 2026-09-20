#!/usr/bin/env bash
set -euo pipefail

EVENT_ID="evt-verify-$(date +%s)"
USER_ID="verify-user-$(date +%s)"
ITEM_ID="${ITEM_ID:-102}"
BEHAVIOR_TOPIC="behavior-events"
CDC_TOPIC="mysql-cdc-ecommerce"

curl -fsS -X POST http://127.0.0.1:8080/api/v1/events \
  -H 'Content-Type: application/json' \
  -d "{
    \"eventId\":\"${EVENT_ID}\",
    \"userId\":\"${USER_ID}\",
    \"sessionId\":\"verify-session\",
    \"itemId\":${ITEM_ID},
    \"eventType\":\"click\",
    \"page\":\"home\",
    \"position\":1,
    \"source\":\"home_card\",
    \"requestId\":\"req-verify\",
    \"recommendationId\":\"rec-verify\",
    \"eventTime\":$(date +%s000)
  }" >/dev/null

echo "event_id=${EVENT_ID}"
echo "user_id=${USER_ID}"

KAFKA_HOME="/opt/homebrew/opt/kafka"
KAFKA_TOPIC_MESSAGE="$(
  "${KAFKA_HOME}/bin/kafka-console-consumer" \
    --bootstrap-server 127.0.0.1:9092 \
    --topic "${BEHAVIOR_TOPIC}" \
    --from-beginning --max-messages 20 --timeout-ms 10000 2>/dev/null \
  | rg "${EVENT_ID}" \
  | tail -1
)"
test -n "${KAFKA_TOPIC_MESSAGE}"
echo "kafka_behavior_event=ok"

for _ in $(seq 1 20); do
  if redis-cli lrange "adrec:user:history:${USER_ID}" 0 -1 | rg -q "^${ITEM_ID}$"; then
    echo "redis_user_history=ok"
    break
  fi
  sleep 1
done
redis-cli lrange "adrec:user:history:${USER_ID}" 0 -1 | rg -q "^${ITEM_ID}$"

MINIO_OBJECT="/opt/homebrew/var/minio/warehouse/realtime/behavior_events/event-${EVENT_ID}.jsonl"
for _ in $(seq 1 20); do
  if [ -e "${MINIO_OBJECT}" ]; then
    echo "minio_raw_event=ok"
    break
  fi
  sleep 1
done
test -e "${MINIO_OBJECT}"

CDC_MESSAGE="$(
  "${KAFKA_HOME}/bin/kafka-console-consumer" \
    --bootstrap-server 127.0.0.1:9092 \
    --topic "${CDC_TOPIC}" \
    --from-beginning --timeout-ms 10000 2>/dev/null \
  | rg "${EVENT_ID}" \
  | tail -1
)"
test -n "${CDC_MESSAGE}"
echo "flink_cdc_to_kafka=ok"
echo "realtime_flow_verified"
