# OncoLake Build Handbook

The exact how-to, starting from the moment you open the unzipped folder in VS
Code. Work top to bottom. Placeholders look like `<THIS>`. Every phase names
the file it uses and the gotcha that usually trips people.

OncoLake mirrors Moffitt's published architecture: heterogeneous sources ->
governed warehouse layers -> a cohort data mart -> a cohort explorer. See
`docs/moffitt_alignment.md` for the diagram and how each piece maps to the JD.

---

## Step 0. Open it in VS Code (5 minutes, free)

1. Unzip and open the folder:
   ```bash
   unzip oncolake-starter.zip
   code oncolake-starter
   ```
2. Install these VS Code extensions (Extensions panel, left sidebar):
   - **Python** (Microsoft)
   - **Snowflake** (Snowflake) - run SQL against your account from the editor
   - **dbt Power User** - preview/compile dbt models
   - **YAML** (Red Hat) - for the dbt and CI configs
3. Create and select a Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   In VS Code, bottom-right, pick the `.venv` interpreter.
4. Read `README.md` and `docs/moffitt_alignment.md` once so the layer names
   (RAW / STAGING / MARTS) make sense before you build.

You now have working code to edit. Nothing is paid yet.

---

## Step 1. Confirm the reusable spine runs (local, free)

You already built the oncology extraction pipeline. Copy your existing `src/`,
`config/`, `reference/`, and `tests/` into this repo (they are the foundation;
this starter only adds the cloud + cohort-mart layers on top). Then:

```bash
bash run_demo.sh          # generate -> deidentify -> extract -> DQ -> evaluate -> load
```
Green run, outputs in `data/synthetic/`. If you do not have that repo handy,
the `data/sample/` files here are enough to test the Snowflake + dbt steps.

Gotcha: run this once now so a later failure is clearly a cloud issue, not
your existing code.

---

## Step 2. Snowflake account + foundations (starts the 30-day clock)

1. Sign up at signup.snowflake.com. **Cloud = AWS, Region = a US region.**
   Cortex model availability is region-dependent; US AWS regions are safest.
2. Open a SQL worksheet in Snowsight (or use the VS Code Snowflake extension)
   and run, in order:
   ```
   snowflake/00_account_setup.sql      -- ONCOLAKE db + RAW/STAGING/MARTS schemas + role
   snowflake/01_warehouses.sql         -- LOAD_WH + QUERY_WH, auto-suspend 60s
   snowflake/02_stages_fileformats.sql -- file formats, internal stage, RAW_CLINICAL_NOTES
   ```
   Edit `<YOUR_USER>` in `00_` before running the grant.
3. Install SnowSQL, then upload the sample notes and run the COPY:
   ```bash
   snowsql -a <account_locator> -u <user>
   # inside snowsql:
   PUT file://data/sample/notes_deidentified.csv @ONCOLAKE.RAW.STG_NOTES_INTERNAL;
   ```
   Then run the `COPY INTO` at the bottom of `02_stages_fileformats.sql`.

Lock cold this week: the 3 layers (storage / compute / cloud services), why
load and query warehouses are separate, micro-partitions and pruning.

---

## Step 3. Add the other source types (multi-format ingestion)

The JD requires ingesting JDBC, API, JSON, and flat files. You now add a JSON
source so you have more than CSV (JDBC comes later via Matillion, streaming
CSV via Snowpipe).

1. Upload and load the JSON pathology report:
   ```
   # in snowsql:
   PUT file://data/sample/pathology_0001.json @ONCOLAKE.RAW.STG_NOTES_INTERNAL;
   ```
   Then run `snowflake/02b_json_source.sql`. It lands the JSON in a VARIANT
   column and flattens it into `STAGING.STG_PATHOLOGY`.

Gotcha: VARIANT + `PARSE_JSON` is the whole "semi-structured" skill. Land it
raw first, flatten in a second step, do not try to type it on ingest.

---

## Step 4. Cortex extraction (the differentiator, do not skip)

File: `snowflake/06_cortex_extract.sql`.

1. Check your region's models. If `claude-3-5-sonnet` errors, swap to
   `llama3.1-70b` or `mistral-large2` (try the Claude one first, it tightens
   your story).
2. Run Approach A (COMPLETE with a JSON-forcing prompt, parsed by
   `TRY_PARSE_JSON`) to build `STAGING.CORTEX_EXTRACTIONS`.
3. Run Approach B (`EXTRACT_ANSWER` + `SENTIMENT`) on a few rows.
4. Load `data/sample/gold_labels.csv` into `STAGING.GOLD_LABELS` and run the
   accuracy join at the bottom of the file. Now you have a Cortex number next
   to your external Claude API 0.908.

The line this earns: "I did clinical-notes extraction externally with the
Claude API at 0.908 F1, then rebuilt the same extraction natively in Snowflake
with Cortex, so it runs in-warehouse with no data leaving Snowflake."

Gotcha: Cortex bills per token. Keep it to the handful of sample notes while
developing.

---

## Step 5. dbt marts, incl. the cohort data mart (reuse + extend)

1. Copy `dbt/oncolake/profiles.example.yml` to `~/.dbt/profiles.yml` and fill
   in account, user, role `ONCOLAKE_ENG`, warehouse `ONCOLAKE_QUERY_WH`,
   database `ONCOLAKE`. The `macros/generate_schema_name.sql` makes `+schema`
   land models in real `STAGING` / `MARTS` schemas (not `PUBLIC_STAGING`).
2. Build:
   ```bash
   cd dbt/oncolake
   dbt deps
   dbt seed        # loads icdo3_topography crosswalk
   dbt run         # stg_cortex_extractions, fct_diagnoses, cohort_data_mart
   dbt snapshot    # builds dim_patient_snapshot (SCD Type 2)
   dbt test
   ```
3. The output you care about is `MARTS.COHORT_DATA_MART`, the wide cohort-ready
   table the explorer reads. This is the OncoLake analog of Moffitt's "Cohort
   data mart".

Gotcha: `dbt snapshot` is a SEPARATE command from `dbt run`. Forget it and your
SCD2 dimension has no history. Change a patient's stage and re-run `dbt
snapshot` to see a second version row: that is your SCD2 talking point.

---

## Step 6. Streamlit cohort explorer (your visible proof)

File: `streamlit/oncolake_app.py`. It reads `MARTS.COHORT_DATA_MART`.

1. Snowsight > Projects > Streamlit > **+ Streamlit App**.
2. Set database `ONCOLAKE`, schema `MARTS`, warehouse `ONCOLAKE_QUERY_WH`.
3. Paste in `oncolake_app.py`, run it. You get KPIs, patients-by-stage,
   treatment breakdown, and a data-quality panel. **This is the screenshot you
   send Swayam.**

Gotcha: if the app is empty, Step 5 did not populate `COHORT_DATA_MART`. Run
`dbt run && dbt snapshot` again.

---

## Step 7. AWS event-driven ingest (Snowpipe + Lambda + Secrets Manager)

Do this before Matillion so Snowpipe has an S3 source. Full click-path in
`aws/sns_sqs_setup.md`. Summary:

1. `aws s3 mb s3://oncolake-landing` (files under `lab_results/`).
2. Run `snowflake/04_snowpipe.sql` to `DESC INTEGRATION`, copy
   `STORAGE_AWS_IAM_USER_ARN` + `STORAGE_AWS_EXTERNAL_ID` into the IAM role's
   trust policy (the "handshake").
3. Run the rest of `04_snowpipe.sql` (external stage + pipe).
4. `SHOW PIPES` -> copy `notification_channel` (SQS ARN) -> add an S3 Event
   notification (all object-create, prefix `lab_results/`) pointing at it.
   Template: `aws/s3_event_notification.json`.
5. Store the JDBC secret: `aws/secrets_manager_setup.md`.
6. Deploy the Lambda: zip `aws/lambda/validate_and_alert.py`, Python 3.12, same
   S3 trigger, grant `secretsmanager:GetSecretValue` + `sns:Publish`.
7. Test: drop `data/sample/lab_results_20260719_a1.csv` into
   `s3://oncolake-landing/lab_results/` and watch:
   ```sql
   SELECT SYSTEM$PIPE_STATUS('ONCOLAKE.RAW.LAB_RESULTS_PIPE');
   SELECT COUNT(*) FROM ONCOLAKE.RAW.RAW_LAB_RESULTS;   -- fills in seconds
   ```
8. Optional incremental merge: run `snowflake/05_streams_tasks.sql`, then
   uncomment the labs join in `cohort_data_mart.sql` and rebuild.

Gotcha: the #1 Snowpipe failure is the trust-policy handshake. Files in S3 but
an empty table almost always means the IAM ARN / external id do not match what
`DESC INTEGRATION` returned.

---

## Step 8. Matillion ELT (start the ~14-day clock LAST)

GUI-driven, so this is a click-path. Sign up for Matillion Data Productivity
Cloud only now. This is where the JDBC source type gets satisfied.

**Orchestration job** `orchestration_load_oncolake`:
1. Create Table (staging target).
2. S3 Load: `s3://oncolake-landing/lab_results/` -> Snowflake staging.
3. Database Query: read a JDBC source, credential pulled from **AWS Secrets
   Manager** (not typed inline).
4. Chain: Start -> Create Table -> S3 Load -> Database Query -> run a
   Transformation job.

**Transformation job** `transformation_stage_to_marts`:
1. Table Input from staging.
2. Convert Type / Calculator for casting.
3. Join lab data to patient data.
4. Detect Changes + SCD component for the Type 2 patient dimension.
5. Table Output into `MARTS`.

Then **export both jobs to JSON** into `matillion/` and screenshot them into
`matillion/screenshots/`. That is what survives after the trial.

Lock cold: orchestration jobs manage flow/control; transformation jobs do the
in-warehouse pushdown (ELT, not ETL). Near-certain interview question.

Gotcha: do not burn trial days reading theory inside Matillion. Learn ELT-vs-
ETL and pushdown from docs first, then spend the trial building.

---

## Step 9. Query profiling (a concrete number)

Files in `snowflake/tuning/`.

1. Run `slow_query.sql`. Snowsight > Query History > that query > **Query
   Profile**. Record partitions scanned, bytes spilled, most expensive
   operator into `before_after.md`.
2. Run `clustered_query.sql` (adds a clustering key, removes the leading-
   wildcard predicate). Re-read the profile, record the "after".
3. Fill in `before_after.md`. That table is your tuning story.

---

## Step 10. Orchestrate, CI, document (completion)

1. `airflow/dags/oncolake_dag.py` triggers the flow end to end.
2. `.github/workflows/ci.yml` runs `pytest -q` on every push (green badge).
3. Update the README with the architecture diagram, a results table, and a
   short design-decisions section. `docs/moffitt_alignment.md` is already
   written; link it from the README.
4. Screenshots into `docs/screenshots/`: Matillion job, Streamlit app,
   Snowpipe load, query profile.

---

## Minimum viable version (one weekend)

If time is tight, in priority order (still gives a true sentence for all three
headline gaps):
1. Matillion loading one CSV to Snowflake with one transformation.
2. The Streamlit app on the cohort mart.
3. One Cortex function over the note text.

Snowpipe, Streams/Tasks, Lambda, Secrets Manager are the stretch goals that
turn "I have read about it" into "I have done it".

---

## Definition of done

- [ ] Four source types land in RAW (notes CSV, lab CSV via Snowpipe, pathology JSON, JDBC via Matillion)
- [ ] Matillion orchestration + transformation jobs, exported JSON + screenshots
- [ ] Cortex extracts stage/site/treatment in SQL, with an accuracy number
- [ ] dbt builds STAGING + MARTS incl. SCD2 patient snapshot and COHORT_DATA_MART, tests passing
- [ ] Streamlit cohort explorer reads the cohort mart, with a data-quality panel
- [ ] Snowpipe auto-loads a file within seconds; Lambda validates + reads its secret
- [ ] before/after query-profile numbers recorded
- [ ] clean README, architecture diagram, screenshots, green CI

Then send Swayam the private repo link with a short note. Keep Challa light and
route the referral through Swayam first.
