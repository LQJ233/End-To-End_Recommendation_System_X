#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATAX_HOME="${PROJECT_ROOT}/data-sync/datax"
JOB_TEMPLATE="${DATAX_HOME}/job/item_full_sync.json"
JOB_RENDERED="$(mktemp -t datax-item-sync-XXXXXX.json)"

# 本地凭据（不纳入版本管理），模板见 .env.local.example
if [ -f "${PROJECT_ROOT}/.env.local" ]; then
  set -a
  . "${PROJECT_ROOT}/.env.local"
  set +a
fi

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-ecommerce}"
MYSQL_USER="${MYSQL_USER:?请设置 MYSQL_USER（环境变量或 .env.local）}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?请设置 MYSQL_PASSWORD（环境变量或 .env.local）}"
export MYSQL_PWD="${MYSQL_PASSWORD}"

mysql -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" -u"${MYSQL_USER}" "${MYSQL_DATABASE}" < \
  "${PROJECT_ROOT}/data-sync/datax/create_sync_table.sql"

# 用本地凭据渲染作业模板（模板中不保存明文密码）
sed -e "s|\${MYSQL_HOST}|${MYSQL_HOST}|g" \
    -e "s|\${MYSQL_PORT}|${MYSQL_PORT}|g" \
    -e "s|\${MYSQL_DATABASE}|${MYSQL_DATABASE}|g" \
    -e "s|\${MYSQL_USER}|${MYSQL_USER}|g" \
    -e "s|\${MYSQL_PASSWORD}|${MYSQL_PASSWORD}|g" \
    "${JOB_TEMPLATE}" > "${JOB_RENDERED}"

python3 "${DATAX_HOME}/bin/datax.py" "${JOB_RENDERED}"
rm -f "${JOB_RENDERED}"
