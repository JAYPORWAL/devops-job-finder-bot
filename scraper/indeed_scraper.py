import requests
from bs4 import BeautifulSoup

class IndeedScraper:
    def __init__(self):
        self.base_url = "https://in.indeed.com/jobs"

    def search(self, query):
        print(f"Scraping Indeed for {query} jobs...")
        params = {"q": query, "l": "India"}
        response = requests.get(self.base_url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        jobs = []
        listings = soup.select("div.job_seen_beacon")

        for listing in listings:
            title_tag = listing.find("h2", class_="jobTitle")
            company_tag = listing.find("span", class_="companyName")
            link_tag = listing.find("a")

            if not title_tag or not company_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            company = company_tag.text.strip()
            link = "https://in.indeed.com" + link_tag["href"]

            jobs.append({
                "title": title,
                "company": company,
                "link": link,
                "source": "Indeed"
            })

        print(f"Found {len(jobs)} Indeed jobs.")
        return jobs


if __name__ == "__main__":
    scraper = IndeedScraper()
    results = scraper.search("DevOps")
    for job in results:
        print(job["title"], "-", job["company"], "-", job["link"])
