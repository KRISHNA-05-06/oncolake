# Query tuning: findings

## What I tested
Ran the same aggregation under different table designs and read the Query Profile each time.

| Scenario | Partitions scanned | Result |
|---|---|---|
| `ILIKE '%psa%'` full scan (16-partition table) | 16 / 16 | Full scan, no pruning |
| Clustered on `test_name` (5 values) | 16 / 16 | No benefit, low cardinality |
| Clustered on `patient_key` (2M values) | n/a | Snowflake warned: high-cardinality key, expensive reclustering |
| Clustered on `clinic_id` (~200 values) | n/a | Snowflake still warned; string key clusters poorly |

## Key findings
1. **Predicate matters most.** Replacing `test_name ILIKE '%psa%'` (leading wildcard, forces scan) with `test_name = 'PSA'` (equality) is the cheapest, most reliable win.
2. **Clustering is a judgment call, not a default.** It only pays off when the table spans many partitions AND the key is *medium* cardinality: selective enough to prune, low enough that reclustering is cheap.
3. **Too-low cardinality** (5 values) → nothing to prune. **Too-high cardinality** (millions, or high-cardinality strings) → Snowflake explicitly warns about expensive reclustering. Integer, medium-cardinality keys cluster best.
4. **Reclustering has a cost.** Measuring immediately after `ALTER ... CLUSTER BY` captures reclustering churn (high remote-disk I/O), not steady-state performance.

## Takeaway
On this dataset, the equality-predicate rewrite was the right optimization; clustering was not justified at this scale. Knowing when *not* to cluster is the point.