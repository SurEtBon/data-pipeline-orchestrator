#!/bin/bash
echo -n $GCP_SERVICE_ACCOUNT_KEY | base64 -d > $GCP_SERVICE_ACCOUNT_KEY_JSON_FILEPATH
cd suretbon && uv run dbt deps && cd ../
uv run airflow scheduler