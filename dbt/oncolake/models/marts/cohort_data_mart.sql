-- COHORT DATA MART
-- This is the OncoLake analog of Moffitt's "Cohort data mart" (Figure 1):
-- the wide, cohort-ready table that the Streamlit explorer (their cBioPortal
-- analog) queries. Joins the current patient version to its diagnosis facts.
--
-- To add lab volume once Phase 5 is built, uncomment the labs CTE + join.
-- with labs as (
--     select patient_id, count(*) as lab_count
--     from {{ source('staging', 'LAB_RESULTS') }}
--     group by 1
-- )
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
