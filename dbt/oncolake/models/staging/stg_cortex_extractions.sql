-- Flattens the Cortex output table into typed columns for the marts.
select
    note_id,
    patient_id,
    primary_site,
    ajcc_stage,
    tnm_stage,
    treatments,
    biomarkers
from {{ source('staging', 'CORTEX_EXTRACTIONS') }}
