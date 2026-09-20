#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 本地凭据（不纳入版本管理），模板见 .env.local.example
if [ -f "${PROJECT_ROOT}/.env.local" ]; then
  set -a
  . "${PROJECT_ROOT}/.env.local"
  set +a
fi

KAFKA_HOME="/opt/homebrew/opt/kafka"
KAFKA_CONFIG="/opt/homebrew/etc/kafka/server.properties"
KAFKA_META="/opt/homebrew/var/lib/kraft-combined-logs/meta.properties"
FLINK_PROJECT="${PROJECT_ROOT}/streaming/flink-realtime"
JAVA_HOME_17="$(/usr/libexec/java_home -v 17)"
export JAVA_HOME="${JAVA_HOME_17}"
export PATH="${JAVA_HOME}/bin:${PATH}"

# 用本地凭据渲染 S3A 配置（仓库里只提交 core-site.xml.template）
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://127.0.0.1:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:?请设置 MINIO_ACCESS_KEY（环境变量或 .env.local）}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:?请设置 MINIO_SECRET_KEY（环境变量或 .env.local）}"
S3A_TEMPLATE="${FLINK_PROJECT}/src/main/resources/core-site.xml.template"
S3A_TARGET="${FLINK_PROJECT}/src/main/resources/core-site.xml"
sed -e "s|\${MINIO_ENDPOINT}|${MINIO_ENDPOINT}|g" \
    -e "s|\${MINIO_ACCESS_KEY}|${MINIO_ACCESS_KEY}|g" \
    -e "s|\${MINIO_SECRET_KEY}|${MINIO_SECRET_KEY}|g" \
    "${S3A_TEMPLATE}" > "${S3A_TARGET}"
echo "rendered ${S3A_TARGET}"

if [ ! -f "${KAFKA_META}" ]; then
  CLUSTER_ID="$("${KAFKA_HOME}/bin/kafka-storage" random-uuid)"
  "${KAFKA_HOME}/bin/kafka-storage" format --standalone -t "${CLUSTER_ID}" -c "${KAFKA_CONFIG}"
fi

brew services run kafka || true

for _ in $(seq 1 30); do
  if "${KAFKA_HOME}/bin/kafka-topics" --bootstrap-server 127.0.0.1:9092 --list >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

"${KAFKA_HOME}/bin/kafka-topics" --bootstrap-server 127.0.0.1:9092 \
  --create --if-not-exists --topic behavior-events --partitions 1 --replication-factor 1
"${KAFKA_HOME}/bin/kafka-topics" --bootstrap-server 127.0.0.1:9092 \
  --create --if-not-exists --topic mysql-cdc-ecommerce --partitions 1 --replication-factor 1

cd "${FLINK_PROJECT}"
mvn -q -s maven-settings.xml package -DskipTests

mkdir -p logs
if ! pgrep -f "com.example.flink.BehaviorRealtimeJob" >/dev/null 2>&1; then
  nohup java -cp target/flink-realtime-0.0.1-SNAPSHOT.jar \
    com.example.flink.BehaviorRealtimeJob \
    > logs/behavior-realtime.log 2>&1 &
  echo $! > logs/behavior-realtime.pid
fi

if ! pgrep -f "com.example.flink.MySqlCdcJob" >/dev/null 2>&1; then
  nohup java -cp target/flink-realtime-0.0.1-SNAPSHOT.jar \
    com.example.flink.MySqlCdcJob \
    > logs/flink-cdc.log 2>&1 &
  echo $! > logs/flink-cdc.pid
fi

echo "Kafka and embedded Flink jobs started."
