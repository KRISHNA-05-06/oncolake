-- slow_query.sql  -- run this first, then open the Query Profile.
-- Deliberately forces a full scan + a large join with no pruning.
USE WAREHOUSE ONCOLAKE_QUERY_WH;

SELECT p.patient_id, COUNT(*) AS lab_count
FROM ONCOLAKE.STAGING.LAB_RESULTS l
JOIN ONCOLAKE.MARTS.DIM_PATIENT p ON l.patient_id = p.patient_id
WHERE l.test_name ILIKE '%psa%'          -- ILIKE + leading wildcard = no pruning
GROUP BY p.patient_id
ORDER BY lab_count DESC;

-- After running: Snowsight > Activity > Query History > click the query >
-- Query Profile. Record: partitions scanned, bytes spilled, most expensive node.
