-- COHORT DATA MART
select
    p.patient_id,
    d.primary_site,
    d.primary_site_code,
    d.ajcc_stage,
    d.tnm_stage,
    d.treatments,
    d.biomarkers,
    p.dbt_valid_from as patient_version_from
    -- , coalesce(l.lab_count, 0) as lab_count
from {{ ref('dim_patient_snapshot') }} p
left join {{ ref('fct_diagnoses') }} d
       on p.patient_id = d.patient_id
-- left join labs l on p.patient_id = l.patient_id
where p.dbt_valid_to is null      -- current version only
