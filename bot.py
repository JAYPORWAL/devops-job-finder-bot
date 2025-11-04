# bot.py
import os
import time
import json
import logging
import html as html_module
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import re

# Scrapers (your existing modules)
from scraper.linkedin_scraper import LinkedInScraper
from scraper.indeed_scraper import IndeedScraper
from scraper.naukri_scraper import NaukriScraper
from scraper.internshala_scraper import InternshalaScraper

# Telegram notifier (your existing module)
from utils.telegram_utils import TelegramNotifier

# Load .env
load_dotenv()

# Logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

# Data dir & seen jobs
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SEEN_FILE = DATA_DIR / "seen_jobs.json"
if not SEEN_FILE.exists():
    with open(SEEN_FILE, "w") as f:
        json.dump({"seen": []}, f)

# Env vars
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "30"))

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
    raise SystemExit("Missing Telegram credentials in .env")

notifier = TelegramNotifier(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

# -----------------------
# Resume-based filters
# -----------------------
# Keywords extracted from the resume (skills, tools, cloud platforms, roles)
RESUME_KEYWORDS = [
    "devops", "devops engineer", "devops intern", "cloud devops", "cloud engineer",
    "aws", "gcp", "google cloud", "google cloud platform", "azure",
    "docker", "kubernetes", "k8s", "ci/cd", "github actions", "gitlab", "jenkins",
    "terraform", "ansible", "infrastructure as code", "iac",
    "linux", "linux admin", "site reliability", "sre", "shell", "bash", "python",
    "nginx", "apache", "docker-compose"
]

# Role keywords prioritized (higher weight)
ROLE_KEYWORDS = [
    "devops engineer", "associate devops", "cloud engineer", "devops intern", "linux",
    "sre", "site reliability", "infrastructure engineer", "platform engineer"
]

# Experience keywords mapping for classification
EXPERIENCE_PATTERNS = {
    "fresher": re.compile(r"\b(fresher|entry level|entry-level|0-1 year|0-6 month|0-6 months|intern)\b", re.I),
    "junior": re.compile(r"\b(junior|associate|jr\.|0-2 years|1-2 years)\b", re.I),
    "mid": re.compile(r"\b(2-5 years|2 years|3 years|4 years|mid[- ]level)\b", re.I),
    "senior": re.compile(r"\b(5\+ years|5 years|senior|lead|principal)\b", re.I)
}

# Heuristic weights for scoring
WEIGHTS = {
    "role_exact": 3,
    "keyword": 1,
    "source_preference": {"linkedin": 1, "naukri": 1, "indeed": 1, "internshala": 1},
    # optional boost if company appears to be hiring grads / interns
    "intern_keyword": 2
}

# Helper: load/save seen ids
def load_seen_ids():
    try:
        with open(SEEN_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("seen", []))
    except Exception:
        return set()

def save_seen_ids(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump({"seen": list(seen_set)}, f, indent=2)

# -----------------------
# Utility functions
# -----------------------
def normalize_text(s):
    return (s or "").lower()

def score_job(job):
    """
    Score a job dict according to resume keywords.
    Returns score (int) and matching keywords list.
    """
    text_fields = " ".join([
        job.get("title") or "",
        job.get("company") or "",
        job.get("snippet") or job.get("description") or "",
        job.get("location") or "",
        job.get("posted_text") or ""
    ]).lower()

    score = 0
    matched = set()

    # role exact matches (higher weight)
    for r in ROLE_KEYWORDS:
        if r in text_fields:
            score += WEIGHTS["role_exact"]
            matched.add(r)

    # generic skills/keyword matches
    for kw in RESUME_KEYWORDS:
        if kw in text_fields:
            score += WEIGHTS["keyword"]
            matched.add(kw)

    # internship keyword boost
    if "intern" in text_fields or "internship" in text_fields:
        score += WEIGHTS["intern_keyword"]
        matched.add("intern")

    # small boost for preferred sources (keeps pluggable)
    source = job.get("source", "").lower()
    score += WEIGHTS["source_preference"].get(source, 0)

    return int(score), sorted(matched)

def parse_experience(job):
    """
    Try to categorize experience level from job text.
    Returns one of: Fresher/Entry, Junior, Mid, Senior, Unknown
    """
    text = normalize_text(" ".join([job.get("title",""), job.get("snippet","") or job.get("description","") or ""]))
    for label, pattern in EXPERIENCE_PATTERNS.items():
        if pattern.search(text):
            if label == "fresher":
                return "Fresher/Entry"
            if label == "junior":
                return "Junior (0-2 yrs)"
            if label == "mid":
                return "Mid (2-5 yrs)"
            if label == "senior":
                return "Senior (5+ yrs)"
    # fallback: try to extract numeric years
    m = re.search(r"(\d+)\+?\s*[-–]?\s*(\d+)?\s*\s*years?", text)
    if m:
        low = int(m.group(1))
        if low <= 1:
            return "Fresher/Entry"
        if low <= 2:
            return "Junior (0-2 yrs)"
        if low <= 5:
            return "Mid (2-5 yrs)"
        return "Senior (5+ yrs)"
    return "Unknown"

def detect_easy_apply(job, timeout=6):
    """
    Heuristic: determine whether job can be applied through LinkedIn 'Easy Apply'
    or whether it requires going to company's external site.
    - If source == linkedin: try quick GET and look for 'Easy Apply' (case-insensitive)
    - If link contains 'apply' or 'apply-now' or 'linkedin' assume easy (heuristic)
    - Otherwise default to 'external'
    Returns "Easy Apply (likely)" or "External apply (visit company site)".
    """
    link = job.get("link") or ""
    source = (job.get("source") or "").lower()

    # quick heuristics:
    if "linkedin" in link or source == "linkedin":
        # try a quick fetch to check content
        try:
            r = requests.get(link, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout)
            text = (r.text or "").lower()
            if "easy apply" in text or "easy-apply" in text:
                return "Easy Apply (LinkedIn)"
            # some linkedin pages may use JS; fallback to heuristic
            if "apply on company site" in text or "apply on company website" in text:
                return "External apply (company site)"
        except Exception:
            # network or blocked; fall back to heuristic
            if "apply" in link.lower():
                return "Easy Apply (likely)"
            return "External apply (likely)"
    # For Internshala, application usually happens on Internshala (easy)
    if "internshala" in link or source == "internshala":
        return "Apply via Internshala"
    # For Naukri / Indeed: sometimes they redirect; assume external unless 'indeedapply' or 'naukri' indicates inline apply
    if "indeed" in link and "apply" in link.lower():
        return "Apply via Indeed"
    if "naukri" in link:
        # Naukri often has an internal apply flow
        return "Apply via Naukri (may require login)"
    return "External apply (visit company site)"

def within_days(job, days=7):
    """
    Check posted_datetime or posted_text if within `days`. If no date, include (conservative).
    """
    posted = job.get("posted_datetime")
    if posted and isinstance(posted, datetime):
        cutoff = datetime.utcnow() - timedelta(days=days)
        return posted >= cutoff
    # try to parse posted_text heuristically like '2 days ago'
    t = (job.get("posted_text") or "").lower()
    if t:
        m = re.search(r"(\d+)\s+day", t)
        if m:
            return int(m.group(1)) <= days
        if "today" in t or "just" in t or "hour" in t or "minutes" in t:
            return True
    # no date info -> include conservatively
    return True

# -----------------------
# Main job cycle
# -----------------------
def job_cycle():
    logger.info("Starting scrape cycle")
    try:
        linkedin = LinkedInScraper()
        indeed = IndeedScraper()
        naukri = NaukriScraper()
        internshala = InternshalaScraper()

        all_jobs = []

        # Collect jobs (each scraper should return list of dicts containing at least title, company, link, source, snippet/description, posted_text/posted_datetime)
        try:
            all_jobs += linkedin.search("DevOps Engineer")
        except Exception as e:
            logger.exception("LinkedIn scraper error: %s", e)

        try:
            all_jobs += indeed.search("DevOps Engineer")
        except Exception as e:
            logger.exception("Indeed scraper error: %s", e)

        try:
            all_jobs += naukri.search("DevOps Engineer")
        except Exception as e:
            logger.exception("Naukri scraper error: %s", e)

        try:
            all_jobs += internshala.search("DevOps")
        except Exception as e:
            logger.exception("Internshala scraper error: %s", e)

        logger.info("Fetched %d total job candidates", len(all_jobs))

        # Filter to last 7 days where possible
        jobs_recent = [j for j in all_jobs if within_days(j, days=7)]
        logger.info("%d jobs after date filter (7 days)", len(jobs_recent))

        # Score & annotate each job
        annotated = []
        for j in jobs_recent:
            score, matches = score_job(j)
            exp = parse_experience(j)
            apply_type = detect_easy_apply(j)
            annotated.append({
                **j,
                "score": score,
                "matches": matches,
                "experience_level": exp,
                "apply_type": apply_type
            })

        # Keep only sufficiently relevant jobs (tunable)
        # We'll keep anything with score >= 1 but prioritize higher scores for sending
        annotated = sorted(annotated, key=lambda x: x["score"], reverse=True)
        logger.info("Top job scores: %s", [a["score"] for a in annotated[:10]])

        # Deduplicate by link (or title+company)
        unique = {}
        for job in annotated:
            key = job.get("link") or f"{job.get('title')}|{job.get('company')}"
            if key not in unique:
                unique[key] = job
        jobs_unique = list(unique.values())
        logger.info("%d unique jobs after dedupe", len(jobs_unique))

        # Load seen ids
        seen = load_seen_ids()
        new_seen = set(seen)
        sent_count = 0

        # Decide which to send
        # Strategy: send top N (or all with score >= threshold). We'll send all with score >=1, with a priority label.
        for job in jobs_unique:
            job_id = job.get("id") or job.get("link")
            if job_id in seen:
                continue

            # Only send if relevance >= 1 (you can adjust)
            if job.get("score", 0) < 1:
                continue

            # Build HTML message
            title = html_module.escape(job.get("title") or "Untitled")
            company = html_module.escape(job.get("company") or "N/A")
            location = html_module.escape(job.get("location") or "N/A")
            snippet = html_module.escape((job.get("snippet") or job.get("description") or "")[:800])
            link = job.get("link") or ""
            posted = html_module.escape(job.get("posted_text") or "")
            source = html_module.escape(job.get("source") or "")
            score = job.get("score", 0)
            matches = ", ".join(job.get("matches", [])) or "—"
            exp = html_module.escape(job.get("experience_level") or "Unknown")
            apply_type = html_module.escape(job.get("apply_type") or "External apply (likely)")

            # Relevance label
            if score >= 6:
                relevance = "🔴 High match"
            elif score >= 3:
                relevance = "🟠 Good match"
            else:
                relevance = "🟢 Possible match"

            message = (
                f"<b>{title}</b>\n"
                f"{company} — {location}\n"
                f"<i>{source}</i> • {posted}\n\n"
                f"{snippet}\n\n"
                f"<b>Relevance:</b> {relevance} (score {score})\n"
                f"<b>Matched:</b> {html_module.escape(matches)}\n"
                f"<b>Experience:</b> {exp}\n"
                f"<b>How to apply:</b> {apply_type}\n"
            )
            if link:
                # Telegram HTML link
                safe_link = html_module.escape(link)
                message += f'\n\u21AA <a href="{safe_link}">View / Apply</a>'

            # Send
            try:
                notifier.send(message)   # uses your existing .send() method which accepts HTML
                logger.info("Sent job: %s - %s (score=%s)", job.get("title"), job.get("company"), score)
                sent_count += 1
                new_seen.add(job_id)
                time.sleep(1)
            except Exception as e:
                logger.exception("Failed sending job to Telegram: %s", e)

        save_seen_ids(new_seen)
        logger.info("Send complete. New jobs sent: %d", sent_count)

    except Exception as e:
        logger.exception("Error during job_cycle: %s", e)

# -----------------------
# Scheduler / main
# -----------------------
def main():
    logger.info("Starting DevOps Job Bot (resume-aware)")
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_cycle, "interval", minutes=SCRAPE_INTERVAL_MINUTES, next_run_time=datetime.utcnow())
    scheduler.start()
    logger.info("Scheduler started: interval %d minutes", SCRAPE_INTERVAL_MINUTES)
    try:
        while True:
            time.sleep(30)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
