-- 05_streams_tasks.sql

USE ROLE ONCOLAKE_ENG;
USE WAREHOUSE ONCOLAKE_LOAD_WH;
USE SCHEMA ONCOLAKE.RAW;

-- Stream tracks inserts into the Snowpipe landing table.
CREATE OR REPLACE STREAM LAB_RESULTS_STREAM ON TABLE RAW_LAB_RESULTS;

-- Target curated table in STAGING.
CREATE TABLE IF NOT EXISTS ONCOLAKE.STAGING.LAB_RESULTS (
  result_id STRING, patient_id STRING, test_name STRING,
  test_value_num FLOAT, collected_at TIMESTAMP_NTZ, merged_at TIMESTAMP_NTZ
);

-- Task consumes the stream every 5 minutes and merges.
CREATE OR REPLACE TASK LAB_RESULTS_MERGE_TASK
  WAREHOUSE = ONCOLAKE_LOAD_WH
  SCHEDULE = '5 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('LAB_RESULTS_STREAM')
AS
  MERGE INTO ONCOLAKE.STAGING.LAB_RESULTS t
  USING (SELECT result_id, patient_id, test_name,
                TRY_TO_DOUBLE(test_value) AS test_value_num, collected_at
         FROM LAB_RESULTS_STREAM WHERE METADATA$ACTION = 'INSERT') s
  ON t.result_id = s.result_id
  WHEN NOT MATCHED THEN
    INSERT (result_id, patient_id, test_name, test_value_num, collected_at, merged_at)
    VALUES (s.result_id, s.patient_id, s.test_name, s.test_value_num, s.collected_at, CURRENT_TIMESTAMP());

ALTER TASK LAB_RESULTS_MERGE_TASK RESUME;  -- tasks are created suspended
