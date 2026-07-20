{% snapshot dim_patient_snapshot %}
{{
  config(
    target_schema='MARTS',
    unique_key='patient_id',
    strategy='check',
    check_cols=['primary_site', 'ajcc_stage', 'tnm_stage']
  )
}}
-- SCD Type 2 patient dimension. dbt manages dbt_valid_from / dbt_valid_to.
-- One row per patient (latest note wins); change a checked column and re-run
-- `dbt snapshot` to open a new version. That history is your SCD2 story.
with ranked as (
    select
        patient_id, primary_site, ajcc_stage, tnm_stage,
        row_number() over (partition by patient_id order by note_id desc) as rn
    from {{ ref('stg_cortex_extractions') }}
)
select patient_id, primary_site, ajcc_stage, tnm_stage,
       current_timestamp() as loaded_at
from ranked
where rn = 1
{% endsnapshot %}
