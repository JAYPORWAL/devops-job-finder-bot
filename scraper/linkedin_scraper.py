# scraper/linkedin_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
)

class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    def __init__(self, sleep_between_requests=1.0):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.sleep = sleep_between_requests

    def search(self, query="devops engineer", location="India", days=7, limit_pages=2):
        """Scrape LinkedIn job listings (guest-accessible API)"""
        jobs = []
        start = 0

        for page in range(limit_pages):
            params = {
                "keywords": query,
                "location": location,
                "start": start,
            }
            url = f"{self.BASE_URL}?keywords={quote_plus(query)}&location={quote_plus(location)}&start={start}"
            try:
                r = self.session.get(url, timeout=15)
                if r.status_code != 200:
                    logger.warning("LinkedIn returned %s for %s", r.status_code, url)
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                job_cards = soup.select("li")

                for card in job_cards:
                    title_tag = card.select_one(".base-search-card__title")
                    title = title_tag.get_text(strip=True) if title_tag else None

                    company_tag = card.select_one(".base-search-card__subtitle")
                    company = company_tag.get_text(strip=True) if company_tag else None

                    loc_tag = card.select_one(".job-search-card__location")
                    location = loc_tag.get_text(strip=True) if loc_tag else None

                    link_tag = card.select_one("a.base-card__full-link")
                    link = link_tag.get("href") if link_tag else None

                    date_tag = card.select_one("time")
                    posted_datetime = None
                    posted_text = None
                    if date_tag:
                        posted_text = date_tag.get("datetime") or date_tag.get_text(strip=True)
                        try:
                            posted_datetime = datetime.fromisoformat(date_tag["datetime"].replace("Z", "+00:00"))
                        except Exception:
                            posted_datetime = None

                    job_id = link or f"linkedin::{title}::{company}"

                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "source": "linkedin",
                        "posted_text": posted_text,
                        "posted_datetime": posted_datetime,
                    })
                start += 25
                time.sleep(self.sleep)
            except Exception as e:
                logger.exception("LinkedIn scraping error: %s", e)
                break

        return jobs
