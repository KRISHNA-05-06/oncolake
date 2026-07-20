-- 02b_json_source.sql
-- Third source type: a semi-structured JSON pathology report. The Moffitt JD
-- explicitly lists "semi-structured file formats (XML, JSON)" as an ingestion
-- requirement, so landing one JSON source proves you handle more than CSV.
-- This mirrors the many heterogeneous "Clinical data sources" hexagons in the
-- Moffitt architecture (Figure 1): different formats, one governed warehouse.

USE ROLE ONCOLAKE_ENG;
USE WAREHOUSE ONCOLAKE_LOAD_WH;
USE SCHEMA ONCOLAKE.RAW;

-- Land the raw JSON as-is in a VARIANT column (keep the source shape for lineage).
CREATE TABLE IF NOT EXISTS RAW_PATHOLOGY_JSON (
  raw        VARIANT,
  _file      STRING,
  _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Load a local JSON file via the internal stage (SnowSQL PUT then COPY):
--   PUT file://data/sample/pathology_0001.json @STG_NOTES_INTERNAL;
COPY INTO RAW_PATHOLOGY_JSON (raw, _file)
  FROM (SELECT $1, METADATA$FILENAME FROM @STG_NOTES_INTERNAL (FILE_FORMAT => FF_JSON))
  PATTERN = '.*pathology.*\\.json';

-- Flatten VARIANT into typed columns (this is the "extract structure from
-- semi-structured" skill). Land it in STAGING for the marts to use.
CREATE OR REPLACE TABLE ONCOLAKE.STAGING.STG_PATHOLOGY AS
SELECT
  raw:report_id::STRING       AS report_id,
  raw:patient_id::STRING      AS patient_id,
  raw:specimen::STRING        AS specimen,
  raw:diagnosis::STRING       AS diagnosis,
  raw:grade::STRING           AS grade,
  raw:collected_at::DATE      AS collected_at
FROM RAW_PATHOLOGY_JSON;
