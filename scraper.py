"""
Fetches fresh job postings from LinkedIn and Naukri for Pune, dedupes them,
and writes the result to data/jobs.csv.

This is meant to be run once a day by the GitHub Actions workflow
(.github/workflows/daily_scrape.yml), NOT by the Streamlit app itself -
Streamlit Community Cloud has no scheduler, so the daily refresh has to
happen in CI and get committed back to the repo.

Run manually with: python scraper.py
"""

import time
import traceback
from datetime import datetime, timezone

import pandas as pd
from jobspy import scrape_jobs

import config

OUTPUT_PATH = "data/jobs.csv"


def fetch_jobs() -> pd.DataFrame:
    all_frames = []

    for term in config.SEARCH_TERMS:
        print(f"Fetching '{term}' in {config.LOCATION} ...")
        try:
            jobs = scrape_jobs(
                site_name=config.SITES,
                search_term=term,
                location=config.LOCATION,
                results_wanted=config.RESULTS_PER_TERM,
                hours_old=config.HOURS_OLD,
                country_indeed="India",
                linkedin_fetch_description=True,
            )
            if jobs is not None and not jobs.empty:
                jobs["search_term"] = term
                all_frames.append(jobs)
                print(f"  -> got {len(jobs)} results")
            else:
                print("  -> 0 results")
        except Exception as e:
            # A single search term failing (rate limit, layout change, etc.)
            # shouldn't kill the whole run - log it and move on.
            print(f"  -> FAILED: {e}")
            traceback.print_exc()

        # Be polite between requests to reduce the chance of getting blocked.
        time.sleep(5)

    if not all_frames:
        print("No jobs fetched from any search term.")
        return pd.DataFrame()

    df = pd.concat(all_frames, ignore_index=True)

    # De-dupe on job_url where available, else on title+company+location.
    if "job_url" in df.columns:
        df = df.drop_duplicates(subset=["job_url"])
    else:
        df = df.drop_duplicates(subset=["title", "company", "location"])

    # Safety net: the site-level location filter isn't always exact
    # (e.g. it can return "Pune, Maharashtra, India" vs "Pune Metropolitan
    # Region" vs remote roles tagged to Pune) - keep only rows that
    # actually mention Pune.
    if "location" in df.columns:
        df = df[df["location"].astype(str).str.contains("pune", case=False, na=False)]

    df["scraped_at"] = datetime.now(timezone.utc).isoformat()

    return df.reset_index(drop=True)


if __name__ == "__main__":
    result = fetch_jobs()
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(result)} Pune job(s) to {OUTPUT_PATH}")
