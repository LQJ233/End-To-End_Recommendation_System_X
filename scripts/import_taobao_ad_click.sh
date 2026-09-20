#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
offline/.venv/bin/python offline/pyspark/create_tables.py
offline/.venv/bin/python offline/pyspark/import_taobao.py
./scripts/import_item_mysql.sh
