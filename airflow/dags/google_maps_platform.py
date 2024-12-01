from airflow import DAG

from airflow.models import Variable

import requests
import json
from datetime import datetime

from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

import time

from airflow.operators.python import PythonOperator

from airflow.operators.trigger_dagrun import TriggerDagRunOperator

GCP_PROJECT_ID = Variable.get("GCP_PROJECT_ID")

GOOGLE_MAPS_PLATFORM_API_KEY = Variable.get("GOOGLE_MAPS_PLATFORM_API_KEY")
GOOGLE_MAPS_PLATFORM_API_LIMIT = Variable.get("GOOGLE_MAPS_PLATFORM_API_LIMIT")

URL = "https://places.googleapis.com/v1/places:searchText"

GCP_BUCKET = Variable.get("GCP_BUCKET")

def create_table_if_not_exists():
    bq = BigQueryHook(use_legacy_sql = False, gcp_conn_id = "google_cloud_default")
    bq.create_empty_table(
        project_id = GCP_PROJECT_ID,
        dataset_id = "raw",
        table_id = "google_maps_platform-place_details",
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
    WITH meta_osm_ids AS (
        SELECT
            gmppd.meta_osm_id,
            MAX(gmppd.created_at) AS created_at
        FROM
            `{GCP_PROJECT_ID}.raw.google_maps_platform-place_details` AS gmppd
        WHERE
            gmppd.created_at >= '{datetime.today().replace(day=1).strftime('%Y-%m-%d')}'
        GROUP BY
            gmppd.meta_osm_id
        ORDER BY
            created_at DESC
    ),
    meta_osm_ids_count AS (
        SELECT
            GREATEST(0, {GOOGLE_MAPS_PLATFORM_API_LIMIT} - COUNT(*)) as result
        FROM
            meta_osm_ids
    ),
    restaurants_to_process AS (
        SELECT
            `osm_ffs-name`,
            `osm_ffs-meta_osm_id`,
            `ea-adresse_2_ua`,
            `ea-code_postal`,
            `ea-com_name`,
            RANK() OVER(ORDER BY `osm_ffs-meta_osm_id` ASC) AS ranking
        FROM
            `{GCP_PROJECT_ID}.intermediate.int_osm-france-food-service_export_alimconfiance`
        WHERE
            `osm_ffs-meta_osm_id` NOT IN (SELECT meta_osm_id FROM meta_osm_ids)
        ORDER BY
            ranking ASC
    )
    SELECT
        *
    FROM
        restaurants_to_process
    WHERE
        ranking <= (SELECT result FROM meta_osm_ids_count)
    """
    results = bq.get_pandas_df(query)

    return results

def get_google_places_informations(restaurants):

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_PLATFORM_API_KEY,
        "X-Goog-FieldMask": "places.accessibilityOptions,places.addressComponents,places.adrFormatAddress,places.businessStatus,places.displayName,places.formattedAddress,places.googleMapsUri,places.iconBackgroundColor,places.iconMaskBaseUri,places.location,places.photos,places.plusCode,places.primaryType,places.primaryTypeDisplayName,places.shortFormattedAddress,places.subDestinations,places.types,places.utcOffsetMinutes,places.viewport,places.currentOpeningHours,places.currentSecondaryOpeningHours,places.internationalPhoneNumber,places.nationalPhoneNumber,places.priceLevel,places.rating,places.regularOpeningHours,places.regularSecondaryOpeningHours,places.userRatingCount,places.websiteUri"
    }

    gcs_hook = GCSHook(gcp_conn_id = "google_cloud_default")
    bigquery_hook = BigQueryHook(gcp_conn_id = "google_cloud_default")

    restaurants_to_bigquery = []

    for index, row in restaurants.iterrows():
        name = row["osm_ffs-name"]
        meta_osm_id = row["osm_ffs-meta_osm_id"]
        adresse_2_ua = row["ea-adresse_2_ua"]
        code_postal = row["ea-code_postal"]
        com_name = row["ea-com_name"]

        data = {
            "textQuery": f"{name} {adresse_2_ua} {code_postal} {com_name}"
        }

        response = requests.post(URL, headers = headers, data = json.dumps(data))

        if response.status_code == 200:
            response_data = response.json()
            
            restaurants_to_bigquery.append({
                "meta_osm_id": meta_osm_id,
                "response": response_data,
                "created_at": datetime.utcnow().isoformat()
            })

            try:
                gcs_hook.upload(
                    bucket_name = GCP_BUCKET,
                    object_name = f"google_maps_platform/place_details/{meta_osm_id}.json",
                    data = json.dumps(response_data),
                    mime_type = "application/json"
                )
            except Exception as e:
                print(f"Erreur pour le restaurant {meta_osm_id}: {str(e)}")

        if len(restaurants_to_bigquery) == 10 or index == (len(restaurants) - 1):
            try:
                bigquery_hook.insert_all(
                    project_id = GCP_PROJECT_ID,
                    dataset_id = "raw",
                    table_id = "google_maps_platform-place_details",
                    rows = restaurants_to_bigquery
                )
            except Exception as e:
                print(f"Erreur lors de l'insertion dans BigQuery {[restaurant["meta_osm_id"] for restaurant in restaurants_to_bigquery]}: {str(e)}")

            restaurants_to_bigquery = []

        time.sleep(0.1)

    return True

def get_google_details():
    create_table_if_not_exists()
    restaurants = get_restaurants_to_process()
    return get_google_places_informations(restaurants)

with DAG(
    "google_maps_platform",
    description = "Get Google Maps Platform Details",
    default_args = { "depends_on_past": True },
    schedule_interval = None,
    start_date = datetime(2024, 12, 2),
    catchup = False
) as dag:

    get_google_details_task = PythonOperator(
        task_id = "get_google_details",
        python_callable = get_google_details,
    )

    trigger_tripadvisor = TriggerDagRunOperator(
        task_id = "trigger_tripadvisor",
        trigger_dag_id = "tripadvisor",
        dag = dag
    )
    
    get_google_details_task >> trigger_tripadvisor