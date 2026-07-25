-- 02_stages_fileformats.sql

USE ROLE ONCOLAKE_ENG;
USE WAREHOUSE ONCOLAKE_LOAD_WH;
USE SCHEMA ONCOLAKE.RAW;

-- File formats: one for the notes CSV, one for JSON if you land nested data.
CREATE OR REPLACE FILE FORMAT FF_CSV
  TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1
  NULL_IF = ('', 'NULL') EMPTY_FIELD_AS_NULL = TRUE;

CREATE OR REPLACE FILE FORMAT FF_JSON TYPE = JSON STRIP_OUTER_ARRAY = TRUE;

-- Internal stage for the manual-load learning step (no AWS needed yet).
CREATE STAGE IF NOT EXISTS STG_NOTES_INTERNAL FILE_FORMAT = FF_CSV;

-- Landing table for the raw clinical notes.
CREATE TABLE IF NOT EXISTS RAW_CLINICAL_NOTES (
  note_id     STRING,
  patient_id  STRING,
  note_date   DATE,
  note_text   STRING,
  _loaded_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  _run_id     STRING
);

-- 1. Upload a local file to the stage (run this in SnowSQL, not the web UI):
--    PUT file://data/synthetic/notes_deidentified.csv @STG_NOTES_INTERNAL;

-- 2. COPY it in. Read the load result: rows_loaded, errors_seen.
COPY INTO RAW_CLINICAL_NOTES (note_id, patient_id, note_date, note_text)
  FROM @STG_NOTES_INTERNAL
  FILE_FORMAT = FF_CSV
  ON_ERROR = 'CONTINUE';

SELECT COUNT(*) AS loaded FROM RAW_CLINICAL_NOTES;
