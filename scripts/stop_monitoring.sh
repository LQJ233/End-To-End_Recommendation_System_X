#!/usr/bin/env bash
#
# Stop Prometheus + Grafana started by scripts/start_monitoring.sh.
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/monitoring/logs"

stop_by_pidfile() {
  local name="$1"
  local pid_file="${LOG_DIR}/${name}.pid"
  if [ -f "${pid_file}" ]; then
    local pid
    pid="$(cat "${pid_file}")"
    if kill -0 "${pid}" >/dev/null 2>&1; then
      kill "${pid}" >/dev/null 2>&1 || true
    fi
    mv "${pid_file}" "${pid_file}.stopped" 2>/dev/null || true
  fi
}

stop_by_pidfile prometheus
stop_by_pidfile grafana

pkill -TERM -f "prometheus --config.file=${PROJECT_ROOT}/monitoring/prometheus/prometheus.yml" 2>/dev/null || true
pkill -TERM -f "grafana server --homepath /opt/homebrew/opt/grafana/share/grafana" 2>/dev/null || true

echo "prometheus and grafana stopped"
