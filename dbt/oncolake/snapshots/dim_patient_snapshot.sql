{% snapshot dim_patient_snapshot %}
{{
  config(
    target_schema='MARTS',
    unique_key='patient_id',
    strategy='check',
    check_cols=['primary_site', 'ajcc_stage', 'tnm_stage']
  )
}}

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
