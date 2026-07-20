import streamlit as st

st.set_page_config(page_title="OncoLake Cohort Explorer", layout="wide")
session = st.connection("snowflake").session()

st.title("OncoLake Cohort Explorer")
st.caption("Synthetic oncology data. No PHI. Reads MARTS.COHORT_DATA_MART.")

MART = "ONCOLAKE.MARTS.COHORT_DATA_MART"

@st.cache_data(ttl=300)
def run(sql):
    return session.sql(sql).to_pandas()

stages = run(f"SELECT DISTINCT ajcc_stage FROM {MART} "
             f"WHERE ajcc_stage IS NOT NULL ORDER BY 1")["AJCC_STAGE"].tolist()
picked = st.multiselect("Filter by AJCC stage", stages, default=stages)
stage_list = ", ".join(f"'{s}'" for s in picked) or "''"

c1, c2, c3 = st.columns(3)
c1.metric("Patients", int(run(f"SELECT COUNT(DISTINCT patient_id) n FROM {MART} WHERE ajcc_stage IN ({stage_list})")["N"][0]))
c2.metric("Primary sites", int(run(f"SELECT COUNT(DISTINCT primary_site) n FROM {MART} WHERE ajcc_stage IN ({stage_list})")["N"][0]))
c3.metric("Stages selected", len(picked))

st.subheader("Patients by cancer stage")
by_stage = run(f"SELECT ajcc_stage, COUNT(DISTINCT patient_id) patients FROM {MART} WHERE ajcc_stage IN ({stage_list}) GROUP BY 1 ORDER BY 1")
st.bar_chart(by_stage.set_index("AJCC_STAGE"))

st.subheader("Treatment breakdown")
tx = run(f"SELECT t.value::string treatment, COUNT(*) n FROM {MART} d, LATERAL FLATTEN(input => d.treatments) t WHERE d.ajcc_stage IN ({stage_list}) GROUP BY 1 ORDER BY 2 DESC LIMIT 15")
if not tx.empty:
    st.bar_chart(tx.set_index("TREATMENT"))

st.subheader("Data quality")
dq = run(f"SELECT AVG(IFF(primary_site IS NULL,1,0)) s, AVG(IFF(ajcc_stage IS NULL,1,0)) a FROM {MART}")
q1, q2 = st.columns(2)
q1.metric("Primary site fill rate", f"{(1-dq['S'][0])*100:.1f}%")
q2.metric("Stage fill rate", f"{(1-dq['A'][0])*100:.1f}%")