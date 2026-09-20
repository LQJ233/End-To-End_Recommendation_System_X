from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_ROOT = "/Users/qj/Item/End-To-End_Recommendation_System_X"
PYSPARK_DIR = f"{PROJECT_ROOT}/offline/pyspark"


with DAG(
    dag_id="initial_warehouse_load",
    description="First full load: CSV -> Iceberg ODS -> DWD -> DWS -> ADS, and MySQL item catalog",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["warehouse", "initial"],
) as dag:
    create_ods = BashOperator(
        task_id="create_ods_tables",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python create_tables.py",
    )

    import_ods = BashOperator(
        task_id="import_taobao_to_ods",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python import_taobao.py",
    )

    build_item_mysql = BashOperator(
        task_id="build_mysql_item_catalog",
        bash_command=f"cd {PROJECT_ROOT} && ./scripts/import_item_mysql.sh && echo mysql_item_done",
    )

    build_dwd = BashOperator(
        task_id="build_dwd",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python build_dwd.py",
    )

    build_dws = BashOperator(
        task_id="build_dws",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python build_dws.py",
    )

    build_ads = BashOperator(
        task_id="build_ads",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python build_ads.py",
    )

    init_pipeline_watermarks = BashOperator(
        task_id="init_pipeline_watermarks",
        bash_command=f"cd {PYSPARK_DIR} && ../.venv/bin/python init_pipeline_watermarks.py",
    )

    create_ods >> import_ods >> build_item_mysql
    import_ods >> build_dwd >> build_dws >> build_ads >> init_pipeline_watermarks
