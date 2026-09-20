import json
import sys
from pathlib import Path
from typing import Any

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pyspark"))

from local_env import mysql_config  # noqa: E402


MYSQL_CONFIG = mysql_config()


def register_model(
    model_name: str,
    version: str,
    artifact_path: str,
    metrics: dict[str, Any],
) -> None:
    connection = pymysql.connect(**MYSQL_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO model_registry
                    (model_name, version, artifact_path, metrics_json, status)
                VALUES (%s, %s, %s, %s, 'active')
                ON DUPLICATE KEY UPDATE
                    artifact_path = VALUES(artifact_path),
                    metrics_json = VALUES(metrics_json),
                    status = 'active'
                """,
                (
                    model_name,
                    version,
                    artifact_path,
                    json.dumps(metrics, ensure_ascii=False),
                ),
            )
            # Only one version per model stays `active`; older versions are
            # kept for rollback/audit but flagged as `archived`.
            cursor.execute(
                """
                UPDATE model_registry
                SET status = 'archived'
                WHERE model_name = %s AND version <> %s AND status <> 'archived'
                """,
                (model_name, version),
            )
        connection.commit()
    finally:
        connection.close()
