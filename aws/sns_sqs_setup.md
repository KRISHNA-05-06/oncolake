# S3 -> event -> Snowpipe wiring (the important AWS bit)

Snowpipe auto-ingest on AWS works through an SQS queue that Snowflake creates
for you. You do NOT create the queue; you point S3 at Snowflake's queue ARN.

1. Create the bucket + prefix:
   aws s3 mb s3://oncolake-landing
   (files go under s3://oncolake-landing/lab_results/)

2. Create the IAM role Snowflake assumes (trust Snowflake's IAM user +
   external id from `DESC INTEGRATION ONCOLAKE_S3_INT`). Give it
   s3:GetObject, s3:GetObjectVersion, s3:ListBucket on the bucket.

3. In Snowflake run 04_snowpipe.sql, then `SHOW PIPES` and copy
   notification_channel (an SQS ARN).

4. In the S3 console: Bucket > Properties > Event notifications > Create:
   - Event types: All object create events
   - Prefix: lab_results/
   - Destination: SQS queue  ->  paste the notification_channel ARN

5. Test: drop a CSV into the prefix and watch RAW_LAB_RESULTS fill within
   seconds. `SELECT SYSTEM$PIPE_STATUS('ONCOLAKE.RAW.LAB_RESULTS_PIPE');`
