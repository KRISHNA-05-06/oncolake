-- One row per patient encounter, joined to the current patient version.
select
    e.note_id           as encounter_id,
    e.patient_id,
    e.primary_site,
    e.ajcc_stage,
    e.tnm_stage,
    p.dbt_valid_from    as patient_version_from
from {{ ref('stg_cortex_extractions') }} e
left join {{ ref('dim_patient_snapshot') }} p
  on e.patient_id = p.patient_id
 and p.dbt_valid_to is null
