-- clustered_query.sql  -- the "after" version.
ALTER TABLE ONCOLAKE.STAGING.LAB_RESULTS CLUSTER BY (test_name);

SELECT p.patient_id, COUNT(*) AS lab_count
FROM ONCOLAKE.STAGING.LAB_RESULTS l
JOIN ONCOLAKE.MARTS.DIM_PATIENT p ON l.patient_id = p.patient_id
WHERE l.test_name = 'PSA'
GROUP BY p.patient_id
ORDER BY lab_count DESC;
