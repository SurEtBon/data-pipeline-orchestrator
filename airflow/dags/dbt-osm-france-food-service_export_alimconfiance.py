import os
from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

DBT_DIR = os.getenv("DBT_DIR")

with DAG(
    "dbt-osm-france-food-service_export_alimconfiance",
    description = "This DAG executes DBT tests and a specific DBT model for restaurant data transformation. It prepares the data that will serve as a basis for searching corresponding information on Google and TripAdvisor. It ensures data quality and processes restaurant information.",
    default_args = { "depends_on_past": True },
    start_date = datetime(2024, 12, 2),
    schedule_interval = None,
    catchup = False
) as dag:
    dbt_test_task = BashOperator(
        task_id = "dbt_test",
        bash_command = f"dbt test --project-dir {DBT_DIR}"
    )

    dbt_run_task = BashOperator(
        task_id = "dbt_run",
        bash_command = f"dbt run --project-dir {DBT_DIR} --selector osm-france-food-service_export_alimconfiance"
    )

    trigger_google_maps_platform = TriggerDagRunOperator(
        task_id = "trigger-google_maps_platform",
        trigger_dag_id = "google_maps_platform",
        dag = dag
    )

    dbt_test_task >> dbt_run_task >> trigger_google_maps_platform