from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator


PROJECT_ROOT = "/Users/qj/Item/End-To-End_Recommendation_System_X"
PYSPARK_DIR = f"{PROJECT_ROOT}/offline/pyspark"


with DAG(
    dag_id="daily_warehouse_and_incremental_train",
    description="Daily rebuild of DWD/DWS/ADS for offline training data",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["warehouse", "daily"],
) as dag:
    start = EmptyOperator(task_id="start")

    import_realtime_events = BashOperator(
        task_id="import_realtime_events",
        bash_command=(
            f"cd {PYSPARK_DIR} && "
            "../.venv/bin/python import_realtime_events.py"
        ),
    )

    build_dwd = BashOperator(
        task_id="build_dwd_incremental",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python build_dwd_incremental.py",
    )

    build_dws = BashOperator(
        task_id="build_dws_incremental",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python build_dws_incremental.py",
    )

    build_ads = BashOperator(
        task_id="build_ads_incremental",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python build_ads_incremental.py",
    )

    incremental_train = BashOperator(
        task_id="incremental_train",
        bash_command=(
            f"cd {PROJECT_ROOT}/offline && "
            ".venv/bin/python -m training.incremental_train --rows 100000 --epochs 1"
        ),
    )

    reload_serving = BashOperator(
        task_id="reload_serving",
        bash_command=(
            "curl -fsS -X POST http://127.0.0.1:8000/v1/models/reload "
            "|| echo 'rec-serving is not running; skip reload'"
        ),
    )

    (
        start
        >> import_realtime_events
        >> build_dwd
        >> build_dws
        >> build_ads
        >> incremental_train
        >> reload_serving
    )
