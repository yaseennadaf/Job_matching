import pandas as pd
import streamlit as st

from resume_matcher import extract_text_from_resume, score_jobs

st.set_page_config(page_title="Pune Job Matcher", page_icon="📍", layout="wide")
st.title("📍 Pune Job Finder")
st.caption("Fresh LinkedIn + Naukri postings for Pune, refreshed daily. Upload your resume to rank by match.")

DATA_PATH = "data/jobs.csv"


@st.cache_data(ttl=3600)
def load_jobs():
    try:
        return pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        return pd.DataFrame()


jobs_df = load_jobs()

if jobs_df.empty:
    st.warning(
        "No job data found yet. Either the daily GitHub Actions scrape hasn't run "
        "yet, or it found nothing matching the configured search terms. "
        "See the README for how to trigger it manually."
    )
    st.stop()

if "scraped_at" in jobs_df.columns:
    st.caption(f"Data last refreshed: {jobs_df['scraped_at'].iloc[0]}")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

sites = sorted(jobs_df["site"].dropna().unique().tolist()) if "site" in jobs_df.columns else []
selected_sites = st.sidebar.multiselect("Source", sites, default=sites)

search_terms = (
    sorted(jobs_df["search_term"].dropna().unique().tolist())
    if "search_term" in jobs_df.columns
    else []
)
selected_terms = st.sidebar.multiselect("Role type", search_terms, default=search_terms)

min_score = st.sidebar.slider("Minimum resume match %", 0, 100, 0)
keyword = st.sidebar.text_input("Keyword filter (title contains)")

# ---------------- Resume upload ----------------
uploaded_resume = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

filtered = jobs_df.copy()

if selected_sites:
    filtered = filtered[filtered["site"].isin(selected_sites)]
if selected_terms:
    filtered = filtered[filtered["search_term"].isin(selected_terms)]
if keyword and "title" in filtered.columns:
    filtered = filtered[filtered["title"].str.contains(keyword, case=False, na=False)]

# Sort by recency by default
if "date_posted" in filtered.columns:
    filtered = filtered.sort_values("date_posted", ascending=False)

if uploaded_resume is not None:
    with st.spinner("Matching your resume against job descriptions..."):
        resume_text = extract_text_from_resume(uploaded_resume)
        text_col = "description" if "description" in filtered.columns else "title"
        filtered = score_jobs(resume_text, filtered, text_column=text_col)
    filtered = filtered[filtered["match_score"] >= min_score]
    st.success(f"Ranked {len(filtered)} job(s) by resume match.")
else:
    st.info("Upload a resume above to rank jobs by relevance. Showing most recent postings for now.")

display_cols = [
    c
    for c in ["match_score", "title", "company", "location", "site", "date_posted", "search_term", "job_url"]
    if c in filtered.columns
]

st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "job_url": st.column_config.LinkColumn("Apply"),
        "match_score": st.column_config.ProgressColumn(
            "Match %", min_value=0, max_value=100, format="%.0f%%"
        )
        if "match_score" in display_cols
        else None,
    },
)

st.caption(f"Showing {len(filtered)} of {len(jobs_df)} total fetched jobs.")

with st.expander("⚠️ Good to know"):
    st.markdown(
        """
- Job data comes from an unofficial scraper (`python-jobspy`). LinkedIn and Naukri
  can rate-limit or change their page structure, which may cause some days to have
  fewer results than others.
- The dataset refreshes once a day via a scheduled GitHub Actions job, not in real time.
- Resume matching uses keyword/text similarity (TF-IDF), not a full semantic understanding
  of your experience — use the match score as a rough ranking signal, not a hard filter.
"""
    )
