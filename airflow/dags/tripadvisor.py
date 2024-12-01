from airflow import DAG

from airflow.models import Variable

import urllib.parse

import requests
import json
from datetime import datetime

from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

import time

from airflow.operators.python import PythonOperator

from airflow.operators.trigger_dagrun import TriggerDagRunOperator

GCP_PROJECT_ID = Variable.get("GCP_PROJECT_ID")

TRIPADISOR_API_KEY = Variable.get("TRIPADISOR_API_KEY")
TRIPADISOR_API_LIMIT = Variable.get("TRIPADISOR_API_LIMIT")

URL = "https://api.content.tripadvisor.com/api/v1"

GCP_BUCKET = Variable.get("GCP_BUCKET")

def create_table_if_not_exists(table_id):
    bq = BigQueryHook(use_legacy_sql = False, gcp_conn_id = "google_cloud_default")
    bq.create_empty_table(
        project_id = GCP_PROJECT_ID,
        dataset_id = "raw",
        table_id = table_id,
        schema_fields = [
            {
                "name": "meta_osm_id",
                "type": "INTEGER",
                "mode": "REQUIRED"
            },
            {
                "name": "response",
                "type": "JSON",
                "mode": "REQUIRED"
            },
            {
                "name": "created_at",
                "type": "DATETIME",
                "mode": "REQUIRED"
            }
        ],
        exists_ok = True
    )
    

def get_restaurants_to_process():
    bq = BigQueryHook(use_legacy_sql = False, gcp_conn_id = "google_cloud_default")
    query = f"""
    WITH tals_meta_osm_ids AS (
        SELECT
            tals.meta_osm_id,
            MAX(tals.created_at) AS created_at
        FROM
            `{GCP_PROJECT_ID}.raw.tripadvisor-location_search` AS tals
        WHERE
            tals.created_at >= '{datetime.today().replace(day=1).strftime('%Y-%m-%d')}'
        GROUP BY
            tals.meta_osm_id
        ORDER BY
            created_at DESC
    ),
    tals_meta_osm_ids_count AS (
        SELECT
            GREATEST(0, {str((int(TRIPADISOR_API_LIMIT) / 2))} - COUNT(*)) as result
        FROM
            tals_meta_osm_ids
    ), tald_meta_osm_ids AS (
        SELECT
            tald.meta_osm_id,
            MAX(tald.created_at) AS created_at
        FROM
            `{GCP_PROJECT_ID}.raw.tripadvisor-location_search` AS tald
        WHERE
            tald.created_at >= '{datetime.today().replace(day=1).strftime('%Y-%m-%d')}'
        GROUP BY
            tald.meta_osm_id
        ORDER BY
            created_at DESC
    ),
    tald_meta_osm_ids_count AS (
        SELECT
            GREATEST(0, {str((int(TRIPADISOR_API_LIMIT) / 2))} - COUNT(*)) as result
        FROM
            tald_meta_osm_ids
    ),
    restaurants_to_process AS (
        SELECT
            `osm_ffs-name`,
            `osm_ffs-meta_geo_point_latitude`,
            `osm_ffs-meta_geo_point_longitude`,
            `osm_ffs-meta_osm_id`,
            RANK() OVER(ORDER BY `osm_ffs-meta_osm_id` ASC) AS ranking
        FROM
            `{GCP_PROJECT_ID}.intermediate.int_osm-france-food-service_export_alimconfiance`
        WHERE
            `osm_ffs-meta_osm_id` NOT IN (SELECT meta_osm_id FROM tals_meta_osm_ids)
        ORDER BY
            ranking ASC
    )
    SELECT
        *
    FROM
        restaurants_to_process
    WHERE
        ranking <= LEAST((SELECT result FROM tals_meta_osm_ids_count), (SELECT result FROM tald_meta_osm_ids_count))
    """
    results = bq.get_pandas_df(query)

    return results

def get_tripadvisor_informations(restaurants):
    location_search_url = f"{URL}/location/search?key={TRIPADISOR_API_KEY}"
    headers = {
        "accept": "application/json"
    }

    gcs_hook = GCSHook(gcp_conn_id = "google_cloud_default")
    bigquery_hook = BigQueryHook(gcp_conn_id = "google_cloud_default")

    restaurants_location_search_to_bigquery = []

    restaurants_location_details_to_bigquery = []

    for index, row in restaurants.iterrows():
        name = row["osm_ffs-name"]
        latitude = row["osm_ffs-meta_geo_point_latitude"]
        longitude = row["osm_ffs-meta_geo_point_longitude"]
        meta_osm_id = row["osm_ffs-meta_osm_id"]

        location_search_url_with_query = f"{location_search_url}&searchQuery={urllib.parse.quote(name)}&latLong={latitude}%2C{longitude}&language=fr"

        location_search_response = requests.get(location_search_url_with_query, headers = headers)

        time.sleep(0.02)

        if location_search_response.status_code == 200:

            location_search_response_data = location_search_response.json()
            
            restaurants_location_search_to_bigquery.append({
                "meta_osm_id": meta_osm_id,
                "response": location_search_response_data,
                "created_at": datetime.utcnow().isoformat()
            })

            try:
                gcs_hook.upload(
                    bucket_name = GCP_BUCKET,
                    object_name = f"tripadvisor/location_search/{meta_osm_id}.json",
                    data = json.dumps(location_search_response_data),
                    mime_type = "application/json"
                )
            except Exception as e:
                print(f"Erreur location_search pour le restaurant {meta_osm_id}: {str(e)}")

        if len(restaurants_location_search_to_bigquery) == 10 or index == (len(restaurants) - 1):
            try:
                bigquery_hook.insert_all(
                    project_id = GCP_PROJECT_ID,
                    dataset_id = "raw",
                    table_id = "tripadvisor-location_search",
                    rows = restaurants_location_search_to_bigquery
                )
            except Exception as e:
                print(f"Erreur location_search lors de l'insertion dans BigQuery: {str(e)}")

            restaurants_location_search_to_bigquery = []

        if 'data' in location_search_response_data:
            if len(location_search_response_data['data']) > 0:
                first_element = location_search_response_data['data'][0]
                if 'location_id' in first_element:
                    location_id = first_element['location_id']
                    location_details_url = f"{URL}/location/{location_id}/details?key={TRIPADISOR_API_KEY}&language=fr&currency=EUR"
                    location_details_response = requests.get(location_details_url, headers = headers)

                    time.sleep(0.02)

                    if location_details_response.status_code == 200:

                        location_details_response_data = location_details_response.json()
                        
                        restaurants_location_details_to_bigquery.append({
                            "meta_osm_id": meta_osm_id,
                            "response": location_details_response_data,
                            "created_at": datetime.utcnow().isoformat()
                        })

                        try:
                            gcs_hook.upload(
                                bucket_name = GCP_BUCKET,
                                object_name = f"tripadvisor/location_details/{meta_osm_id}.json",
                                data = json.dumps(location_details_response_data),
                                mime_type = "application/json"
                            )
                        except Exception as e:
                            print(f"Erreur location_details pour le restaurant {meta_osm_id}: {str(e)}")

        if len(restaurants_location_details_to_bigquery) == 10 or index == (len(restaurants) - 1):
            try:
                bigquery_hook.insert_all(
                    project_id = GCP_PROJECT_ID,
                    dataset_id = "raw",
                    table_id = "tripadvisor-location_details",
                    rows = restaurants_location_details_to_bigquery
                )
            except Exception as e:
                print(f"Erreur location_details lors de l'insertion dans BigQuery: {str(e)}")

            restaurants_location_details_to_bigquery = []

    return True

def get_tripadvisor_details():
    create_table_if_not_exists("tripadvisor-location_search")
    create_table_if_not_exists("tripadvisor-location_details")
    restaurants = get_restaurants_to_process()
    return get_tripadvisor_informations(restaurants)

with DAG(
    "tripadvisor",
    description = "Get Tripadvisor Details",
    default_args = { "depends_on_past": True },
    schedule_interval = None,
    start_date = datetime(2024, 12, 2),
    catchup = False
) as dag:

    get_tripadvisor_details_task = PythonOperator(
        task_id = "get_tripadvisor_details",
        python_callable = get_tripadvisor_details,
    )

    trigger_dbt_restaurants = TriggerDagRunOperator(
        task_id = "trigger-dbt-restaurants",
        trigger_dag_id = "dbt-restaurants",
        dag = dag
    )
    
    get_tripadvisor_details_task >> trigger_dbt_restaurants