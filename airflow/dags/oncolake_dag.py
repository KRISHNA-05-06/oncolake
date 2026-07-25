"""End-to-end orchestration for the OncoLake pipeline.

Two tasks: pull the clinical notes out of RAW and write structured fields to
STAGING.CORTEX_EXTRACTIONS, then let dbt build the marts on top of that table.
Ingestion into RAW is not a task here because it happens outside Airflow, either
event-driven through Snowpipe or on Matillion's own schedule.

Scheduled manually rather than on a cron: the extract task calls the Claude API
once per note, so an unattended nightly run would spend money re-extracting a
table that only changes when new notes land.
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="oncolake_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["oncolake", "moffitt"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command="python src/extract_to_snowflake.py",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "cd dbt/oncolake && dbt seed && dbt run && dbt snapshot && dbt test"
        ),
    )

    extract >> dbt_build
