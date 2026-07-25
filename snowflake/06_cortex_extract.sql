-- 06_cortex_extract.sql

USE ROLE ONCOLAKE_ENG;
USE WAREHOUSE ONCOLAKE_QUERY_WH;
USE SCHEMA ONCOLAKE.STAGING;

-- Approach A: COMPLETE with a JSON-forcing prompt, then parse.
CREATE OR REPLACE TABLE CORTEX_EXTRACTIONS AS
WITH prompted AS (
  SELECT
    note_id,
    patient_id,
    SNOWFLAKE.CORTEX.COMPLETE(
      'claude-3-5-sonnet',
      CONCAT(
        'You are a cancer registry abstractor. From the clinical note, return ONLY ',
        'valid JSON with keys: primary_site, histology, tnm_stage, ajcc_stage, ',
        'treatments (array), biomarkers (array). No prose. Note:\n', note_text
      )
    ) AS raw_json
  FROM ONCOLAKE.RAW.RAW_CLINICAL_NOTES
)
SELECT
  note_id,
  patient_id,
  raw_json,
  TRY_PARSE_JSON(raw_json)                              AS parsed,
  TRY_PARSE_JSON(raw_json):primary_site::STRING         AS primary_site,
  TRY_PARSE_JSON(raw_json):ajcc_stage::STRING           AS ajcc_stage,
  TRY_PARSE_JSON(raw_json):tnm_stage::STRING            AS tnm_stage,
  TRY_PARSE_JSON(raw_json):treatments                   AS treatments,
  TRY_PARSE_JSON(raw_json):biomarkers                   AS biomarkers
FROM prompted;

-- Approach B: EXTRACT_ANSWER for a single targeted field (nice to show both).
SELECT
  note_id,
  SNOWFLAKE.CORTEX.EXTRACT_ANSWER(note_text, 'What is the cancer stage?') AS stage_answer,
  SNOWFLAKE.CORTEX.SENTIMENT(note_text)                                   AS note_sentiment
FROM ONCOLAKE.RAW.RAW_CLINICAL_NOTES
LIMIT 5;
