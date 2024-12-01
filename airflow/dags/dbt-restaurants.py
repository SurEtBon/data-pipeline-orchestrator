import os
from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator

DBT_DIR = os.getenv("DBT_DIR")

with DAG(
    "dbt-restaurants",
    description = "",
    default_args = { "depends_on_past": True },
    start_date = datetime(2024, 12, 2),
    schedule_interval = None,
    catchup = False
) as dag:

    dbt_run_task = BashOperator(
        task_id = "dbt_run",
        bash_command = f"dbt run --project-dir {DBT_DIR} --selector restaurants"
    )

    dbt_run_task