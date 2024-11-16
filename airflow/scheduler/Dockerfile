FROM python:3.12.7-slim

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

ENV AIRFLOW_HOME=/opt/airflow

ENV DBT_DIR=$AIRFLOW_HOME/suretbon
ENV DBT_TARGET_DIR=$DBT_DIR/target
ENV DBT_PROFILES_DIR=$DBT_DIR
ENV DBT_VERSION=1.8.8

WORKDIR $AIRFLOW_HOME

COPY ./pyproject.toml ./pyproject.toml

RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get install -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv venv \
    && uv pip install -r pyproject.toml

COPY ./airflow/scheduler/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh