"""oncolake_dag.py -- end-to-end orchestration."""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="oncolake_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,          # trigger manually while building
    catchup=False,
    tags=["oncolake", "moffitt"],
) as dag:

    generate   = BashOperator(task_id="generate",   bash_command="python -m src.generate_synthetic_notes")
    deidentify = BashOperator(task_id="deidentify", bash_command="python -m src.deidentify")
    extract    = BashOperator(task_id="extract",     bash_command="python -m src.extract_llm && python -m src.extract_baseline")
    quality    = BashOperator(task_id="quality",     bash_command="python -m src.data_quality")
    load       = BashOperator(task_id="load",        bash_command="python -m src.load_snowflake")
    dbt_build  = BashOperator(task_id="dbt_build",   bash_command="cd dbt/oncolake && dbt seed && dbt run && dbt snapshot && dbt test")

    generate >> deidentify >> extract >> quality >> load >> dbt_build
