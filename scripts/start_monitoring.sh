#!/usr/bin/env bash
#
# Start Prometheus + Grafana for the recommendation system (single machine).
#
# Uses `brew`-installed binaries but deliberately does NOT use
# `brew services start`, so nothing is registered as a login/startup service.
# Everything is launched in the background with pid files under
# monitoring/logs, and can be stopped with scripts/stop_monitoring.sh.
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MONITORING_DIR="${PROJECT_ROOT}/monitoring"
LOG_DIR="${MONITORING_DIR}/logs"

# 本地凭据（不纳入版本管理），模板见 .env.local.example
if [ -f "${PROJECT_ROOT}/.env.local" ]; then
  set -a
  . "${PROJECT_ROOT}/.env.local"
  set +a
fi

PROMETHEUS_CONFIG="${MONITORING_DIR}/prometheus/prometheus.yml"
PROMETHEUS_DATA="${MONITORING_DIR}/prometheus/data"

GRAFANA_HOMEPATH="/opt/homebrew/opt/grafana/share/grafana"
GRAFANA_PROVISIONING="${MONITORING_DIR}/grafana/provisioning"
GRAFANA_DASHBOARDS="${MONITORING_DIR}/grafana/dashboards"
GRAFANA_DATA="${MONITORING_DIR}/grafana/data"
GRAFANA_LOGS="${MONITORING_DIR}/grafana/logs"
GRAFANA_PLUGINS="${MONITORING_DIR}/grafana/plugins"

mkdir -p "${LOG_DIR}" "${PROMETHEUS_DATA}"
mkdir -p "${GRAFANA_DATA}" "${GRAFANA_LOGS}" "${GRAFANA_PLUGINS}"

start_prometheus() {
  if pgrep -f "prometheus --config.file=${PROMETHEUS_CONFIG}" >/dev/null 2>&1; then
    echo "prometheus already running"
    return
  fi
  nohup /opt/homebrew/bin/prometheus \
    --config.file="${PROMETHEUS_CONFIG}" \
    --storage.tsdb.path="${PROMETHEUS_DATA}" \
    --web.listen-address="127.0.0.1:9090" \
    > "${LOG_DIR}/prometheus.log" 2>&1 &
  echo $! > "${LOG_DIR}/prometheus.pid"
  echo "prometheus started (pid $(cat "${LOG_DIR}/prometheus.pid"))"
}

start_grafana() {
  if pgrep -f "grafana server --homepath ${GRAFANA_HOMEPATH}" >/dev/null 2>&1; then
    echo "grafana already running"
    return
  fi
  GF_PATHS_PROVISIONING="${GRAFANA_PROVISIONING}" \
  GF_PATHS_DATA="${GRAFANA_DATA}" \
  GF_PATHS_LOGS="${GRAFANA_LOGS}" \
  GF_PATHS_PLUGINS="${GRAFANA_PLUGINS}" \
  GF_SERVER_HTTP_ADDR="127.0.0.1" \
  GF_SERVER_HTTP_PORT="3000" \
  GF_SECURITY_ADMIN_USER="admin" \
  GF_SECURITY_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:?请设置 GRAFANA_ADMIN_PASSWORD（环境变量或 .env.local）}" \
  GF_ANALYTICS_REPORTING_ENABLED="false" \
  GF_ANALYTICS_CHECK_FOR_UPDATES="false" \
  nohup /opt/homebrew/bin/grafana server \
    --homepath "${GRAFANA_HOMEPATH}" \
    > "${LOG_DIR}/grafana.log" 2>&1 &
  echo $! > "${LOG_DIR}/grafana.pid"
  echo "grafana started (pid $(cat "${LOG_DIR}/grafana.pid"))"
}

start_prometheus
start_grafana

for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:9090/-/ready >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
echo "prometheus ready: http://127.0.0.1:9090"

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:3000/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
echo "grafana ready: http://127.0.0.1:3000 (admin/admin)"
echo "dashboards dir: ${GRAFANA_DASHBOARDS}"
