-- Diagnosis fact: one row per abstracted note, coded to ICD-O-3 topography.
select
    e.note_id            as diagnosis_id,
    e.patient_id,
    e.primary_site,
    x.icdo3_code         as primary_site_code,
    e.ajcc_stage,
    e.tnm_stage,
    e.treatments,
    e.biomarkers
from {{ ref('stg_cortex_extractions') }} e
left join {{ ref('icdo3_topography') }} x
       on lower(e.primary_site) = lower(x.site_label)
