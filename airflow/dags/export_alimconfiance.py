from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from datetime import datetime
import requests
import os

URL = "https://dgal.opendatasoft.com/api/explore/v2.1/catalog/datasets/export_alimconfiance/exports/parquet?lang=fr&timezone=Europe%2FBerlin"

GCP_BUCKET = Variable.get("GCP_BUCKET")

GCP_PROJECT_ID = Variable.get("GCP_PROJECT_ID")

def download_file_to_gcs(**context):
    execution_date = context['execution_date'].strftime('%Y-%m-%d')
    filename = f"{execution_date}.parquet"
    file = f"/tmp/export_alimconfiance-{filename}"
    
    response = requests.get(URL)

    with open(file, "wb") as f:
        f.write(response.content)

    object_name = f"export_alimconfiance/{filename}"
    
    gcs_hook = GCSHook(gcp_conn_id = "google_cloud_default")
    gcs_hook.upload(
        bucket_name = GCP_BUCKET,
        object_name = object_name,
        filename = file
    )
    
    os.remove(file)

    context["task_instance"].xcom_push(key = "object_name", value = object_name)

with DAG(
    "export_alimconfiance",
    description = "It downloads food safety inspection data from the French government's, uploads it to Google Cloud Storage, loads it into BigQuery. Finally, it triggers a dbt DAG for further tests and processing.",
    default_args = { "depends_on_past": True },
    schedule_interval = "0 18 * * *",
    start_date = datetime(2024, 12, 2),
    catchup = False
) as dag:
    download_file_to_gcs_task = PythonOperator(
        task_id = "download_file_to_gcs",
        python_callable = download_file_to_gcs,
        provide_context = True
    )

    load_file_from_gcs_to_bigquery_task = GCSToBigQueryOperator(
        task_id = "load_file_from_gcs_to_bigquery",
        bucket = GCP_BUCKET,
        source_objects = ["{{ task_instance.xcom_pull(task_ids='download_file_to_gcs', key='object_name') }}"],
        destination_project_dataset_table = f"{GCP_PROJECT_ID}.raw.export_alimconfiance",
        source_format = "PARQUET",
        write_disposition = "WRITE_TRUNCATE",
        autodetect = True,
        gcp_conn_id = "google_cloud_default"
    )

    trigger_dbt_osm_france_food_service_export_alimconfiance = TriggerDagRunOperator(
        task_id = "trigger-dbt-osm-france-food-service_export_alimconfiance",
        trigger_dag_id = "dbt-osm-france-food-service_export_alimconfiance",
        dag = dag
    )

    download_file_to_gcs_task >> load_file_from_gcs_to_bigquery_task >> trigger_dbt_osm_france_food_service_export_alimconfiance