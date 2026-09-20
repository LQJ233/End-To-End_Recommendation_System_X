#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 本地凭据（不纳入版本管理），模板见 .env.local.example
if [ -f "${PROJECT_ROOT}/.env.local" ]; then
  set -a
  . "${PROJECT_ROOT}/.env.local"
  set +a
fi

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_DATABASE="${MYSQL_DATABASE:-ecommerce}"
MYSQL_USER="${MYSQL_USER:?请设置 MYSQL_USER（环境变量或 .env.local）}"
export MYSQL_PWD="${MYSQL_PASSWORD:?请设置 MYSQL_PASSWORD（环境变量或 .env.local）}"

mysql -h"${MYSQL_HOST}" -u"${MYSQL_USER}" "${MYSQL_DATABASE}" -e "TRUNCATE TABLE item"

cd "$PROJECT_ROOT"
offline/.venv/bin/python offline/pyspark/import_item_mysql.py

COUNT="$(mysql -h"${MYSQL_HOST}" -u"${MYSQL_USER}" "${MYSQL_DATABASE}" -N -e "SELECT COUNT(*) FROM item")"
echo "MySQL item rows: ${COUNT}"
