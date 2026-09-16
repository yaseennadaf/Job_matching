from pathlib import Path

import pandas as pd
import streamlit as st

from resume_matcher import extract_text_from_resume, score_jobs

st.set_page_config(page_title="Pune Job Matcher", page_icon="📍", layout="wide")
st.title("📍 Pune Job Finder")
st.caption(
    "Fresh LinkedIn + Naukri postings for Pune, refreshed daily. "
    "Upload your resume to rank by match."
)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "jobs.csv"
DISMISSED_PATH = BASE_DIR / "data" / "dismissed_jobs.txt"


def load_dismissed() -> set[str]:
    """Load the permanent dismissed list that lives in the GitHub repo."""
    if DISMISSED_PATH.exists():
        try:
            lines = DISMISSED_PATH.read_text(encoding="utf-8").splitlines()
            return {line.strip() for line in lines if line.strip()}
        except Exception:
            return set()
    return set()


@st.cache_data(ttl=3600)
def load_jobs():
    if not DATA_PATH.exists():
        return pd.DataFrame(), f"File not found: {DATA_PATH}"
    try:
        df = pd.read_csv(DATA_PATH)
        if df.empty:
            return df, "File exists but is empty (0 rows)."
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"Failed to read CSV: {type(e).__name__}: {e}"


# ---------- Load data ----------
jobs_df, load_error = load_jobs()

if jobs_df.empty:
    st.warning("No job data found yet.")
    st.markdown(
        """
Trigger the **Scrape Pune Jobs** workflow from the Actions tab, then hard-refresh this page.
        """
    )
    if load_error:
        st.info(f"Diagnostic: {load_error}")
    st.stop()

if "scraped_at" in jobs_df.columns:
    st.caption(f"Data last refreshed: {jobs_df['scraped_at'].iloc[0]}")

# ---------- Permanent dismissed list (from GitHub) ----------
# Always start from the file that is committed in the repo
permanent_dismissed = load_dismissed()

# Session can hold *additional* dismissals that have not been committed yet
if "pending_dismissed" not in st.session_state:
    st.session_state.pending_dismissed = set()

# Combined set used for filtering
all_dismissed = permanent_dismissed | st.session_state.pending_dismissed

# Filter out dismissed jobs
filtered = jobs_df.copy()
if "job_url" in filtered.columns and all_dismissed:
    filtered = filtered[\~filtered["job_url"].isin(all_dismissed)]

# ---------- Resume upload & matching ----------
uploaded_resume = st.file_uploader(
    "Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"]
)

if "date_posted" in filtered.columns:
    filtered = filtered.sort_values("date_posted", ascending=False)

if uploaded_resume is not None:
    with st.spinner("Matching your resume against job descriptions..."):
        resume_text = extract_text_from_resume(uploaded_resume)
        text_col = "description" if "description" in filtered.columns else "title"
        filtered = score_jobs(resume_text, filtered, text_column=text_col)
    st.success(f"Ranked {len(filtered)} job(s) by resume match.")
else:
    st.info("Upload a resume above to rank jobs by relevance. Showing most recent postings for now.")

# ---------- Display ----------
display_cols = [
    c
    for c in [
        "match_score",
        "title",
        "company",
        "location",
        "site",
        "date_posted",
        "search_term",
        "job_url",
    ]
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

st.caption(
    f"Showing {len(filtered)} of {len(jobs_df)} total jobs "
    f"({len(all_dismissed)} permanently hidden)."
)

# ---------- Don't show again ----------
st.divider()
st.subheader("Don't show again")

if "job_url" in filtered.columns and not filtered.empty:
    options = filtered["job_url"].tolist()
    label_map = {
        row["job_url"]: f"{row.get('title', 'Unknown')} @ {row.get('company', 'Unknown')}"
        for _, row in filtered.iterrows()
    }

    selected = st.multiselect(
        "Select jobs you never want to see again",
        options=options,
        format_func=lambda url: label_map.get(url, url),
        placeholder="Choose jobs to hide…",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Hide selected jobs", type="primary", disabled=not selected):
            st.session_state.pending_dismissed.update(selected)
            st.success(f"Hidden {len(selected)} job(s) for this session.")
            st.rerun()

    with col2:
        # Build the full list that should be committed to GitHub
        new_full_list = sorted(permanent_dismissed | st.session_state.pending_dismissed)
        if new_full_list:
            st.download_button(
                label="Download updated dismissed_jobs.txt (commit this to GitHub)",
                data="\n".join(new_full_list),
                file_name="dismissed_jobs.txt",
                mime="text/plain",
                help="Download → replace data/dismissed_jobs.txt in your repo → commit & push. "
                     "After that the jobs stay hidden forever, even after reboots.",
            )
else:
    st.caption("No jobs left to hide.")

# Show current pending count so the user knows they need to commit
if st.session_state.pending_dismissed:
    st.info(
        f"You have **{len(st.session_state.pending_dismissed)}** newly hidden job(s) "
        "that are only saved for this session. "
        "Download the file above and commit it to `data/dismissed_jobs.txt` "
        "to make them permanent."
    )

with st.expander("⚠️ How permanent hiding works"):
    st.markdown(
        """
1. Select jobs → click **Hide selected jobs** (they disappear immediately).
2. Click **Download updated dismissed_jobs.txt**.
3. In your GitHub repo replace the file `data/dismissed_jobs.txt` with the downloaded one.
4. Commit & push.
5. After the next Streamlit refresh the jobs stay hidden forever (even after container reboots).

The app itself cannot push to GitHub — that is a Streamlit Cloud limitation.
        """
        )  of your experience — use the match score as a rough ranking signal, not a hard filter.
"""
    )
