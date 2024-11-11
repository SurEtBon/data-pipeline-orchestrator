# data-pipeline-orchestrator
ETL pipeline orchestration using Apache Airflow and DBT. Handles data extraction, transformation, and loading with automated workflows and data quality checks.

<table>
    <thead>
        <tr>
            <th>Environment variables</th>
            <th>Value</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>GCP_PROJECT_ID</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td>GCP_SERVICE_ACCOUNT_KEY_JSON_FILEPATH</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td>GCP_SERVICE_ACCOUNT_KEY</td>
            <td></td>
            <td></td>
        </tr>
    </tbody>
</table>

```ShellSession
cd suretbon && uv run dbt deps && uv run dbt test
```

```ShellSession
cd suretbon && uv run dbt run --selector restaurants_without_google_and_tripadvisor
```

```ShellSession
cd suretbon && uv run dbt run --selector restaurants
```

```ShellSession
cd suretbon && uv run dbt clean
```

```ShellSession
rm -rf suretbon/logs
```

```ShellSession
rm -f suretbon/.user.yml
```