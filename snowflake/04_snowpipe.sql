-- 04_snowpipe.sql
-- Auto-ingest from S3. Order matters: storage integration -> external
-- stage -> pipe -> then wire the S3 event to the pipe's SQS channel.

USE ROLE ACCOUNTADMIN;

-- 1. Storage integration. STORAGE_AWS_ROLE_ARN is an IAM role you create in
--    AWS that trusts Snowflake. After creating this, run DESC INTEGRATION and
--    copy STORAGE_AWS_IAM_USER_ARN + STORAGE_AWS_EXTERNAL_ID back into that
--    role's trust policy.
CREATE OR REPLACE STORAGE INTEGRATION ONCOLAKE_S3_INT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<ACCOUNT_ID>:role/oncolake-snowflake-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://oncolake-landing/lab_results/');

DESC INTEGRATION ONCOLAKE_S3_INT;  -- copy the two ARN/ExternalId values to AWS

GRANT USAGE ON INTEGRATION ONCOLAKE_S3_INT TO ROLE ONCOLAKE_ENG;

-- 2. External stage pointing at the S3 prefix.
USE ROLE ONCOLAKE_ENG;
USE SCHEMA ONCOLAKE.RAW;

CREATE OR REPLACE STAGE STG_LAB_RESULTS_S3
  STORAGE_INTEGRATION = ONCOLAKE_S3_INT
  URL = 's3://oncolake-landing/lab_results/'
  FILE_FORMAT = FF_CSV;

-- 3. Landing table for streaming lab-result files.
CREATE TABLE IF NOT EXISTS RAW_LAB_RESULTS (
  result_id STRING, patient_id STRING, test_name STRING,
  test_value STRING, collected_at TIMESTAMP_NTZ,
  _file STRING, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 4. The pipe. AUTO_INGEST = TRUE is the whole point.
CREATE OR REPLACE PIPE ONCOLAKE.RAW.LAB_RESULTS_PIPE
  AUTO_INGEST = TRUE
  AS
  COPY INTO RAW_LAB_RESULTS (result_id, patient_id, test_name, test_value, collected_at, _file)
  FROM (
    SELECT $1, $2, $3, $4, $5, METADATA$FILENAME
    FROM @STG_LAB_RESULTS_S3
  )
  FILE_FORMAT = FF_CSV;

-- 5. Get the SQS notification channel ARN, then in AWS add an S3 event
--    notification (ObjectCreated) on the bucket pointing at THIS ARN.
SHOW PIPES;
-- copy the notification_channel value -> S3 bucket > Properties > Event notifications
