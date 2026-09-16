# Edit this list to change what job titles get searched for every day.
# Keep it fairly broad - the resume matcher (in the Streamlit app) does the
# fine-grained relevance ranking on top of whatever gets fetched here.
SEARCH_TERMS = [
    "Software Engineer",
    "Python Developer",
    "Data Analyst",
    "Data Scientist",
    "Business Analyst",
    "Backend Developer",
    "Full Stack Developer",
]

# jobspy location string - "Pune, India" works for both LinkedIn and Naukri
LOCATION = "Pune, India"

# How many results to pull PER search term, PER site. Keep this modest -
# LinkedIn/Naukri rate-limit aggressively. 30-50 is a reasonable daily amount.
RESULTS_PER_TERM = 30

# Only fetch jobs posted within this many hours (freshness filter).
# 24 = "posted in the last day". Raise to 48-72 if you want more volume,
# e.g. on a Monday to catch weekend postings.
HOURS_OLD = 24

# Sites to scrape. jobspy also supports indeed, glassdoor, zip_recruiter,
# google, bayt, bdjobs if you want to add more sources later.
SITES = ["linkedin", "naukri"]
