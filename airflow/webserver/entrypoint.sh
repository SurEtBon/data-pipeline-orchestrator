#!/bin/bash
uv run airflow db upgrade
uv run airflow users create -r Admin -u $AIRFLOW_ADMIN_USERNAME -p $AIRFLOW_ADMIN_PASSWORD -e $AIRFLOW_ADMIN_EMAIL -f $AIRFLOW_ADMIN_FIRST_NAME -l $AIRFLOW_ADMIN_LAST_NAME
uv run airflow connections add 'google_cloud_default' \
    --conn-type 'google_cloud_platform' \
    --conn-extra "{
        \"extra__google_cloud_platform__keyfile_dict\": $(echo $GCP_SERVICE_ACCOUNT_KEY | base64 -d),
        \"extra__google_cloud_platform__project\": \"${GCP_PROJECT_ID}\"
    }"
uv run airflow variables set GCP_PROJECT_ID $GCP_PROJECT_ID
uv run airflow variables set GCP_BUCKET $GCP_BUCKET
uv run airflow variables set GOOGLE_MAPS_PLATFORM_API_KEY $GOOGLE_MAPS_PLATFORM_API_KEY
uv run airflow variables set TRIPADISOR_API_KEY $TRIPADISOR_API_KEY
uv run airflow webserver