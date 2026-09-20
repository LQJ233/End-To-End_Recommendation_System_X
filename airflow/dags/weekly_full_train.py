from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator


PROJECT_ROOT = "/Users/qj/Item/End-To-End_Recommendation_System_X"


with DAG(
    dag_id="weekly_full_train",
    description="Weekly full model training on one million behavior rows and Rec Serving reload",
    schedule="0 3 * * 0",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["training", "weekly"],
) as dag:
    start = EmptyOperator(task_id="start")
    full_train = BashOperator(
        task_id="full_train",
        bash_command=(
            f"cd {PROJECT_ROOT}/offline && "
            ".venv/bin/python -m training.train --epochs 2 --batch-size 8192"
        ),
    )
    reload_serving = BashOperator(
        task_id="reload_serving",
        bash_command=(
            "curl -fsS -X POST http://127.0.0.1:8000/v1/models/reload "
            "|| echo 'rec-serving is not running; skip reload'"
        ),
    )
    end = EmptyOperator(task_id="end")

    start >> full_train >> reload_serving >> end
