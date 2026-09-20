#!/usr/bin/env bash
set -euo pipefail

for pid_file in \
  /Users/qj/Item/End-To-End_Recommendation_System_X/streaming/flink-realtime/logs/behavior-realtime.pid \
  /Users/qj/Item/End-To-End_Recommendation_System_X/streaming/flink-realtime/logs/flink-cdc.pid
do
  if [ -f "${pid_file}" ]; then
    PID="$(cat "${pid_file}")"
    if kill -0 "${PID}" >/dev/null 2>&1; then
      kill "${PID}"
    fi
    mv "${pid_file}" "${pid_file}.stopped" 2>/dev/null || true
  fi
done

pkill -TERM -f "com.example.flink.BehaviorRealtimeJob" 2>/dev/null || true
pkill -TERM -f "com.example.flink.MySqlCdcJob" 2>/dev/null || true
brew services stop kafka || true
echo "Kafka and embedded Flink jobs stopped."
