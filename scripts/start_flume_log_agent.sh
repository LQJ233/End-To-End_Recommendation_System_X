#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JAVA_HOME_17="$(/usr/libexec/java_home -v 17)"
export JAVA_HOME="${JAVA_HOME_17}"
export PATH="${JAVA_HOME}/bin:${PATH}"

mkdir -p "${PROJECT_ROOT}/data-sync/flume/spool"
mkdir -p "${PROJECT_ROOT}/data-sync/flume/logs"

exec "$(brew --prefix flume)/libexec/bin/flume-ng" agent \
  --conf "${PROJECT_ROOT}/data-sync/flume/conf" \
  --conf-file "${PROJECT_ROOT}/data-sync/flume/conf/flume-kafka.conf" \
  --name a1 \
  -Dflume.root.logger=INFO,console
