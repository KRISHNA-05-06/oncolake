"""extract_to_snowflake.py

Free-path replacement for Snowflake Cortex (blocked on trial accounts).
Reads clinical notes from ONCOLAKE.RAW.RAW_CLINICAL_NOTES, extracts structured
fields with the Claude API, and writes them into STAGING.CORTEX_EXTRACTIONS,
the same table the Cortex SQL would have produced. Everything downstream
(dbt marts, cohort mart, Streamlit) reads that table and works unchanged.

Run:
    python src/extract_to_snowflake.py

Requires these environment variables (set in your shell before running):
    ANTHROPIC_API_KEY   your Claude API key
    SNOWFLAKE_ACCOUNT   your account locator, e.g. ab12345.us-east-1
    SNOWFLAKE_USER      your Snowflake username
    SNOWFLAKE_PASSWORD  your Snowflake password
"""
import os
import json
import anthropic
import snowflake.connector

MODEL = "claude-sonnet-4-6"

PROMPT = (
    "You are a cancer registry abstractor. From the clinical note, return ONLY "
    "valid JSON with keys: primary_site (string), histology (string), "
    "tnm_stage (string), ajcc_stage (string), treatments (array of strings), "
    "biomarkers (array of strings). No prose, no markdown. Note:\n\n{note}"
)


def connect_snowflake():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role="ONCOLAKE_ENG",
        warehouse="ONCOLAKE_QUERY_WH",
        database="ONCOLAKE",
        schema="STAGING",
    )


def extract(client, note_text):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": PROMPT.format(note=note_text)}],
    )
    raw = msg.content[0].text.strip()
    # strip any accidental code fences
    raw = raw.replace("```json", "").replace("```", "").strip()
    return raw


def main():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    conn = connect_snowflake()
    cur = conn.cursor()

    # Create the target table (matches what the Cortex SQL builds).
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ONCOLAKE.STAGING.CORTEX_EXTRACTIONS (
            note_id      STRING,
            patient_id   STRING,
            raw_json     STRING,
            parsed       VARIANT,
            primary_site STRING,
            ajcc_stage   STRING,
            tnm_stage    STRING,
            treatments   VARIANT,
            biomarkers   VARIANT
        )
    """)
    # Idempotent: clear so re-runs don't duplicate.
    cur.execute("TRUNCATE TABLE ONCOLAKE.STAGING.CORTEX_EXTRACTIONS")

    cur.execute("SELECT note_id, patient_id, note_text "
                "FROM ONCOLAKE.RAW.RAW_CLINICAL_NOTES")
    rows = cur.fetchall()
    print(f"Extracting {len(rows)} notes with {MODEL} ...")

    for note_id, patient_id, note_text in rows:
        raw = extract(client, note_text)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  {note_id}: could not parse JSON, storing raw only")
            parsed = {}
        cur.execute(
            """
            INSERT INTO ONCOLAKE.STAGING.CORTEX_EXTRACTIONS
              (note_id, patient_id, raw_json, parsed, primary_site,
               ajcc_stage, tnm_stage, treatments, biomarkers)
            SELECT %s, %s, %s, PARSE_JSON(%s), %s, %s, %s,
                   PARSE_JSON(%s), PARSE_JSON(%s)
            """,
            (
                note_id, patient_id, raw, raw,
                parsed.get("primary_site"),
                parsed.get("ajcc_stage"),
                parsed.get("tnm_stage"),
                json.dumps(parsed.get("treatments", [])),
                json.dumps(parsed.get("biomarkers", [])),
            ),
        )
        print(f"  {note_id}: {parsed.get('primary_site')} / "
              f"{parsed.get('ajcc_stage')}")

    conn.commit()
    cur.close()
    conn.close()
    print("Done. Loaded into ONCOLAKE.STAGING.CORTEX_EXTRACTIONS")


if __name__ == "__main__":
    main()