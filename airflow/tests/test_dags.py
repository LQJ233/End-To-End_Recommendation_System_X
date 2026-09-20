import os
from pathlib import Path

os.environ.setdefault(
    "AIRFLOW_HOME",
    "/Users/qj/Item/End-To-End_Recommendation_System_X/airflow",
)

from airflow.models.dagbag import DagBag


DAGS_DIR = Path(__file__).resolve().parents[1] / "dags"


def dagbag():
    return DagBag(dag_folder=str(DAGS_DIR), include_examples=False)


def test_all_dags_load_without_import_errors():
    bag = dagbag()

    assert bag.import_errors == {}
    assert set(bag.dag_ids) == {
        "initial_warehouse_load",
        "daily_warehouse_and_incremental_train",
        "weekly_full_train",
    }


def test_initial_warehouse_load_has_expected_chain():
    dag = dagbag().get_dag("initial_warehouse_load")

    assert set(dag.task_ids) == {
        "create_ods_tables",
        "import_taobao_to_ods",
        "build_mysql_item_catalog",
        "build_dwd",
        "build_dws",
        "build_ads",
        "init_pipeline_watermarks",
    }
    assert dag.get_task("create_ods_tables").downstream_task_ids == {"import_taobao_to_ods"}
    assert dag.get_task("build_dws").downstream_task_ids == {"build_ads"}


def test_daily_warehouse_load_contains_training_placeholder():
    dag = dagbag().get_dag("daily_warehouse_and_incremental_train")

    assert dag.get_task("start").downstream_task_ids == {"import_realtime_events"}
    assert dag.get_task("import_realtime_events").downstream_task_ids == {
        "build_dwd_incremental"
    }
    assert dag.get_task("build_ads_incremental").downstream_task_ids == {
        "incremental_train"
    }
    assert dag.get_task("incremental_train").downstream_task_ids == {"reload_serving"}


def test_weekly_full_train_executes_real_training_and_reloads_serving():
    dag = dagbag().get_dag("weekly_full_train")

    assert set(dag.task_ids) == {"start", "full_train", "reload_serving", "end"}
    assert dag.get_task("full_train").downstream_task_ids == {"reload_serving"}
