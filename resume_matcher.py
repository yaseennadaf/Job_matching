"""
Resume parsing + job matching.

Uses TF-IDF + cosine similarity rather than a transformer model on purpose:
it needs no downloaded model weights, runs fast, and stays well within
Streamlit Community Cloud's free-tier memory limit (~1GB RAM).
"""

import re

import docx2txt
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_resume(uploaded_file) -> str:
    """uploaded_file is a Streamlit UploadedFile object."""
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text

    if name.endswith(".docx"):
        return docx2txt.process(uploaded_file)

    if name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT resume.")


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip().lower()


def score_jobs(resume_text: str, jobs_df, text_column: str = "description"):
    """
    Returns a copy of jobs_df with a new 'match_score' column (0-100),
    sorted highest match first.
    """
    jobs_df = jobs_df.copy()

    if text_column not in jobs_df.columns or jobs_df.empty:
        jobs_df["match_score"] = 0.0
        return jobs_df

    resume_clean = _clean(resume_text)
    job_texts = jobs_df[text_column].fillna("").apply(_clean).tolist()

    # Fall back to title if descriptions are missing/empty for a row -
    # some Naukri postings come through with a thin description field.
    if "title" in jobs_df.columns:
        job_texts = [
            jt if jt.strip() else _clean(t)
            for jt, t in zip(job_texts, jobs_df["title"].fillna(""))
        ]

    corpus = [resume_clean] + job_texts
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    jobs_df["match_score"] = (sims * 100).round(1)

    return jobs_df.sort_values("match_score", ascending=False).reset_index(drop=True)
