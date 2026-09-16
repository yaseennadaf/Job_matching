# Pune Job Matcher

Daily-refreshed job feed from LinkedIn + Naukri, filtered to **Pune**, with resume-based match scoring in a Streamlit app.

## How it actually works (read this first)

There is no official LinkedIn or Naukri API for this kind of search, and both sites'
Terms of Service prohibit automated scraping. This project uses
[`python-jobspy`](https://github.com/speedyapply/JobSpy), the most actively maintained
open-source scraper for job boards, which works most of the time but:

- Can get rate-limited (HTTP 429) or return fewer/zero results some days.
- Can break when LinkedIn/Naukri change their page structure — if that happens, check
  for a `jobspy` update (`pip install -U python-jobspy`).
- Should be run sparingly (once a day, modest result counts) to reduce the chance of
  your IP getting temporarily blocked.

**Streamlit Community Cloud cannot run a daily cron job itself** — it only serves the app,
and the app sleeps when nobody's using it. So the architecture is:

```
GitHub Actions (daily cron, 9am IST)
   → runs scraper.py
   → fetches jobs, filters to Pune
   → commits data/jobs.csv back to the repo
        ↓
Streamlit Community Cloud app (app.py)
   → reads data/jobs.csv
   → lets you upload a resume
   → ranks jobs by TF-IDF text similarity to your resume
```

Streamlit auto-redeploys are not needed for the data update — the app reads the CSV
fresh (cached 1 hour) on each load, so once GitHub Actions commits new data, the next
page load picks it up.

## Setup

1. **Push this folder to a new GitHub repo** (public repo recommended — Actions minutes
   are free and unlimited on public repos; private repos get a limited free quota).

2. **Enable Actions**: GitHub → your repo → Actions tab → enable workflows if prompted.
   The workflow at `.github/workflows/daily_scrape.yml` runs automatically at 9:00 AM IST
   daily, or you can trigger it manually anytime from the Actions tab
   ("Run workflow" button) — do this once right after pushing, so you have data
   immediately instead of waiting for tomorrow's schedule.

3. **Deploy to Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - "New app" → point it at your repo, branch `main`, main file `app.py`
   - Deploy. That's it — no secrets or API keys are needed for this version.

4. **Customize your search** by editing `config.py`:
   - `SEARCH_TERMS`: the job titles searched daily (add/remove based on your target roles)
   - `HOURS_OLD`: freshness window (24 = last day, 72 = last 3 days)
   - `RESULTS_PER_TERM`: how many results per title per site (keep modest, 20–30)

   Commit and push changes — the next scheduled Actions run (or a manual trigger)
   will pick up the new config.

## Using the app

- Open the deployed Streamlit link.
- Upload your resume (PDF, DOCX, or TXT).
- Jobs get scored 0–100% based on text similarity between your resume and each job's
  description, and re-sorted by that score.
- Use the sidebar to filter by source (LinkedIn/Naukri), role type, or a minimum match %.

## Known limitations, honestly

- **Match scoring is keyword/TF-IDF based**, not a deep semantic understanding of your
  experience. It's a decent relevance signal, not a hard filter — a 40% match can still
  be a great fit if your resume is short or uses different wording than the job post.
- **"Pune" filtering is double-enforced**: once via the search location, once via a
  post-filter checking the location string contains "Pune" — but some remote/hybrid
  roles tagged loosely by LinkedIn/Naukri may still slip through or get excluded.
- **Data can go stale or sparse** if scraping gets blocked on a given day. If `data/jobs.csv`
  looks outdated, check the Actions tab for failed runs.
- If you want more reliable long-term data, the sustainable alternative is a paid
  aggregator API (e.g. Adzuna, JSearch on RapidAPI) instead of scraping — those have
  official ToS-compliant access, at the cost of a subscription and less exact
  LinkedIn/Naukri coverage.

## File structure

```
.
├── app.py                          # Streamlit app
├── scraper.py                      # Scrapes jobs, run by GitHub Actions
├── resume_matcher.py               # Resume parsing + TF-IDF match scoring
├── config.py                       # Search terms, location, freshness settings
├── requirements.txt
├── data/
│   └── jobs.csv                    # Latest scraped data (auto-updated by Actions)
└── .github/workflows/
    └── daily_scrape.yml            # Daily cron job
```
